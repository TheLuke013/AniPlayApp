# modules/ui/video_player.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QComboBox, QFrame,
                               QProgressBar, QMessageBox, QWidget)
from PySide6.QtCore import Qt, QUrl, QTimer, QTime, QPropertyAnimation, QEasingCurve
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QIcon, QPalette, QColor
from loguru import logger

class VideoPlayerDialog(QDialog):
    def __init__(self, video_data, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.media_player = None
        self.audio_output = None
        self.is_playing = False
        self.is_fullscreen = False
        self.current_quality = None
        self.current_language = 'dublado'  # Padrão dublado
        self.was_playing_before_minimize = False
        self.controls_visible = True
        self.mouse_inactivity_timer = QTimer()
        self.controls_animation = None
        
        self.setup_ui()
        self.setup_media_player()
        self.setup_animations()
        self.load_video()
        
    def setup_ui(self):
        self.setWindowTitle("Player de Anime")
        self.setMinimumSize(1000, 650)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Widget de vídeo
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                background: #000000;
                border: none;
            }
        """)
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
        self.video_widget.setMouseTracking(True)
        
        main_layout.addWidget(self.video_widget, 1)
        
        # Controles
        self.controls_widget = self.create_controls()
        self.controls_widget.setMouseTracking(True)
        main_layout.addWidget(self.controls_widget)
        
        self.setLayout(main_layout)
        
        # Timer para atualizar controles
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_controls)
        self.update_timer.start(100)
        
        # Timer para ocultar controles em tela cheia
        self.mouse_inactivity_timer.timeout.connect(self.hide_controls)
        self.mouse_inactivity_timer.setSingleShot(True)
        
        # Instala event filter para detectar movimento do mouse
        self.video_widget.installEventFilter(self)
        self.controls_widget.installEventFilter(self)
        self.installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Detecta movimento do mouse para mostrar/ocultar controles"""
        if event.type() in [event.Type.MouseMove, event.Type.MouseButtonPress]:
            self.show_controls_temporarily()
        return super().eventFilter(obj, event)
    
    def setup_animations(self):
        """Configura animações para os controles"""
        self.controls_animation = QPropertyAnimation(self.controls_widget, b"maximumHeight")
        self.controls_animation.setDuration(300)
        self.controls_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def show_controls_temporarily(self):
        """Mostra controles temporariamente em tela cheia"""
        if self.is_fullscreen:
            if not self.controls_visible:
                self.show_controls()
            # Reinicia o timer de inatividade
            self.mouse_inactivity_timer.start(3000)  # 3 segundos
    
    def show_controls(self):
        """Mostra controles com animação"""
        if not self.controls_visible:
            self.controls_animation.setStartValue(0)
            self.controls_animation.setEndValue(100)
            self.controls_animation.start()
            self.controls_visible = True
    
    def hide_controls(self):
        """Oculta controles com animação (apenas em tela cheia)"""
        if self.is_fullscreen and self.controls_visible:
            self.controls_animation.setStartValue(100)
            self.controls_animation.setEndValue(0)
            self.controls_animation.start()
            self.controls_visible = False
    
    def create_controls(self):
        """Cria a barra de controles"""
        controls = QWidget()
        controls.setFixedHeight(100)
        controls.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 26, 26, 220), stop:1 rgba(10, 10, 10, 220));
                border-top: 1px solid #333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 8, 15, 12)
        layout.setSpacing(8)
        
        # Barra de progresso
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(10)
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                font-weight: bold;
                min-width: 40px;
            }
        """)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #404040;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ff7b00;
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }
            QSlider::sub-page:horizontal {
                background: #ff7b00;
                border-radius: 3px;
            }
        """)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)
        
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                font-weight: bold;
                min-width: 40px;
            }
        """)
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider, 1)
        progress_layout.addWidget(self.total_time_label)
        
        # Controles principais
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(15)
        
        # Lado esquerdo - Controles de reprodução
        left_controls = QHBoxLayout()
        left_controls.setSpacing(8)
        
        self.play_btn = QPushButton("⏸️")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #ff7b00;
                border: none;
                border-radius: 20px;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background: #ff9500;
            }
            QPushButton:pressed {
                background: #e66a00;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        
        self.rewind_btn = QPushButton("⏪ 10s")
        self.rewind_btn.setFixedSize(70, 30)
        self.rewind_btn.setStyleSheet("""
            QPushButton {
                background: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444444;
                border: 1px solid #666666;
            }
        """)
        self.rewind_btn.clicked.connect(self.rewind_10s)
        
        self.forward_btn = QPushButton("⏩ 10s")
        self.forward_btn.setFixedSize(70, 30)
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444444;
                border: 1px solid #666666;
            }
        """)
        self.forward_btn.clicked.connect(self.forward_10s)
        
        left_controls.addWidget(self.play_btn)
        left_controls.addWidget(self.rewind_btn)
        left_controls.addWidget(self.forward_btn)
        
        # Centro - Informações
        center_controls = QHBoxLayout()
        center_controls.setSpacing(15)
        
        # Controle de volume
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(5)
        
        self.volume_btn = QPushButton("🔊")
        self.volume_btn.setFixedSize(30, 30)
        self.volume_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #cccccc;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        self.volume_btn.clicked.connect(self.toggle_mute)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #404040;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #cccccc;
                width: 12px;
                height: 12px;
                border-radius: 6px;
                margin: -4px 0;
            }
            QSlider::sub-page:horizontal {
                background: #ff7b00;
                border-radius: 2px;
            }
        """)
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        volume_layout.addWidget(self.volume_btn)
        volume_layout.addWidget(self.volume_slider)
        
        center_controls.addLayout(volume_layout)
        
        # Lado direito - Outros controles
        right_controls = QHBoxLayout()
        right_controls.setSpacing(10)
        
        # Qualidade
        quality_layout = QHBoxLayout()
        quality_layout.setSpacing(5)
        
        quality_label = QLabel("Qualidade:")
        quality_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        
        self.quality_combo = QComboBox()
        self.quality_combo.setFixedSize(80, 25)
        self.quality_combo.setStyleSheet("""
            QComboBox {
                background: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 15px;
            }
            QComboBox QAbstractItemView {
                background: #333333;
                color: white;
                border: 1px solid #555555;
                selection-background-color: #ff7b00;
            }
        """)
        self.quality_combo.currentTextChanged.connect(self.change_quality)
        
        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        
        # Idioma - AGORA FUNCIONAL
        self.language_btn = QPushButton("🇧🇷 Dub")
        self.language_btn.setFixedSize(60, 25)
        self.language_btn.setStyleSheet("""
            QPushButton {
                background: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444444;
            }
        """)
        self.language_btn.clicked.connect(self.toggle_language)
        
        # Tela cheia
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedSize(35, 25)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: #333333;
                color: white;
                border: 1px solid #555555;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #444444;
            }
        """)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        right_controls.addLayout(quality_layout)
        right_controls.addWidget(self.language_btn)
        right_controls.addWidget(self.fullscreen_btn)
        
        # Adiciona tudo ao layout principal
        controls_layout.addLayout(left_controls)
        controls_layout.addStretch()
        controls_layout.addLayout(center_controls)
        controls_layout.addStretch()
        controls_layout.addLayout(right_controls)
        
        layout.addLayout(progress_layout)
        layout.addLayout(controls_layout)
        
        controls.setLayout(layout)
        return controls
    
    def setup_media_player(self):
        """Configura o player de mídia com tratamento robusto de erros"""
        try:
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)
            
            # Configurações para melhor compatibilidade
            self.media_player.setProperty("videoOutput", "software")
            
            # Conecta sinais
            self.media_player.positionChanged.connect(self.position_changed)
            self.media_player.durationChanged.connect(self.duration_changed)
            self.media_player.playbackStateChanged.connect(self.playback_state_changed)
            self.media_player.errorOccurred.connect(self.handle_player_error)
            
            # Configura volume inicial
            self.set_volume(80)
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar media player: {e}")
            self.show_error(f"Erro na configuração do player: {str(e)}")
    
    def load_video(self):
        """Carrega o vídeo baseado nos dados fornecidos"""
        try:
            streaming_links = self.video_data.get('streaming_links', {})
            
            if not streaming_links:
                self.show_error("Nenhum link de streaming disponível")
                return
            
            # Preenche o seletor de qualidade
            self.quality_combo.clear()
            for quality in streaming_links.keys():
                self.quality_combo.addItem(quality)
            
            # Tenta carregar a melhor qualidade primeiro
            preferred_qualities = ['F-HD', 'HD', 'SD']
            for quality in preferred_qualities:
                if quality in streaming_links:
                    self.current_quality = quality
                    self.quality_combo.setCurrentText(quality)
                    self.play_stream(streaming_links[quality])
                    break
            
            if not self.current_quality and streaming_links:
                # Usa o primeiro link disponível
                first_quality = list(streaming_links.keys())[0]
                self.current_quality = first_quality
                self.quality_combo.setCurrentText(first_quality)
                self.play_stream(streaming_links[first_quality])
                
        except Exception as e:
            logger.error(f"❌ Erro ao carregar vídeo: {e}")
            self.show_error(f"Erro ao carregar vídeo: {str(e)}")
    
    def play_stream(self, stream_url):
        """Reproduz um stream URL com tratamento robusto"""
        try:
            logger.info(f"🎬 Carregando stream: {stream_url[:100]}...")
            
            # Para qualquer reprodução anterior de forma segura
            if self.media_player:
                self.media_player.stop()
                # Pequeno delay para limpeza
                QTimer.singleShot(50, lambda: self._start_stream(stream_url))
                
        except Exception as e:
            logger.error(f"❌ Erro no play_stream: {e}")
            self.show_error(f"Erro ao carregar stream: {str(e)}")
    
    def _start_stream(self, stream_url):
        """Inicia o stream após limpeza"""
        try:
            self.media_player.setSource(QUrl(stream_url))
            # Pequeno delay antes de reproduzir
            QTimer.singleShot(100, self.media_player.play)
            logger.info("✅ Stream configurado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro no _start_stream: {e}")
    
    def toggle_play_pause(self):
        """Alterna entre play e pause"""
        if not self.media_player:
            return
            
        try:
            if self.media_player.playbackState() == QMediaPlayer.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()
        except Exception as e:
            logger.error(f"❌ Erro ao alternar play/pause: {e}")
    
    def rewind_10s(self):
        """Volta 10 segundos"""
        if self.media_player:
            try:
                current_pos = self.media_player.position()
                self.media_player.setPosition(max(0, current_pos - 10000))
            except Exception as e:
                logger.error(f"❌ Erro ao retroceder: {e}")
    
    def forward_10s(self):
        """Avança 10 segundos"""
        if self.media_player:
            try:
                current_pos = self.media_player.position()
                duration = self.media_player.duration()
                self.media_player.setPosition(min(duration, current_pos + 10000))
            except Exception as e:
                logger.error(f"❌ Erro ao avançar: {e}")
    
    def set_volume(self, volume):
        """Ajusta o volume"""
        if self.audio_output:
            try:
                self.audio_output.setVolume(volume / 100.0)
                # Atualiza ícone do volume
                if volume == 0:
                    self.volume_btn.setText("🔇")
                elif volume < 50:
                    self.volume_btn.setText("🔈")
                else:
                    self.volume_btn.setText("🔊")
            except Exception as e:
                logger.error(f"❌ Erro ao ajustar volume: {e}")
    
    def toggle_mute(self):
        """Alterna entre mudo e com som"""
        if self.audio_output:
            try:
                if self.audio_output.isMuted():
                    self.audio_output.setMuted(False)
                    self.set_volume(self.volume_slider.value())
                else:
                    self.audio_output.setMuted(True)
                    self.volume_btn.setText("🔇")
            except Exception as e:
                logger.error(f"❌ Erro ao alternar mudo: {e}")
    
    def on_slider_pressed(self):
        """Quando o usuário pressiona a barra de progresso"""
        self.was_playing_before_seek = self.media_player.playbackState() == QMediaPlayer.PlayingState
        if self.was_playing_before_seek:
            self.media_player.pause()
    
    def on_slider_released(self):
        """Quando o usuário solta a barra de progresso"""
        if hasattr(self, 'was_playing_before_seek') and self.was_playing_before_seek:
            self.media_player.play()
    
    def on_slider_moved(self, position):
        """Quando o usuário move a barra de progresso - AGORA FUNCIONAL"""
        if self.media_player:
            try:
                # Atualiza o tempo atual imediatamente
                current_time = QTime(0, 0, 0, 0).addMSecs(position)
                self.current_time_label.setText(current_time.toString("mm:ss"))
                
                # Define a posição no player
                self.media_player.setPosition(position)
            except Exception as e:
                logger.error(f"❌ Erro ao mover slider: {e}")
    
    def change_quality(self, quality):
        """Muda a qualidade do vídeo"""
        if quality != self.current_quality:
            streaming_links = self.video_data.get('streaming_links', {})
            if quality in streaming_links:
                self.current_quality = quality
                current_position = self.media_player.position()
                self.play_stream(streaming_links[quality])
                # Restaura a posição após carregar
                QTimer.singleShot(2000, lambda: self.media_player.setPosition(current_position))
    
    def toggle_language(self):
        """Alterna entre legendado e dublado - AGORA FUNCIONAL"""
        try:
            # Primeiro para a reprodução atual
            was_playing = self.media_player.playbackState() == QMediaPlayer.PlayingState
            current_position = self.media_player.position()
            
            # Alterna o idioma
            if self.current_language == 'dublado':
                self.current_language = 'legendado'
                self.language_btn.setText("🇧🇷 Leg")
                logger.info("🔄 Alternando para LEGENDADO")
            else:
                self.current_language = 'dublado'
                self.language_btn.setText("🇧🇷 Dub")
                logger.info("🔄 Alternando para DUBLADO")
            
            # Obtém o episódio atual
            episode_data = self.video_data.get('episode_data', {})
            episode_number = episode_data.get('number', 1)
            anime_name = self.video_data.get('anime_name', '')
            
            # Gera novo link baseado no idioma
            from modules.anime.animefire_downloader import AnimeFireDownloader
            downloader = AnimeFireDownloader()
            
            if self.current_language == 'dublado':
                new_url = f"https://animefire.plus/animes/{anime_name}-dublado/{episode_number}"
            else:
                new_url = f"https://animefire.plus/animes/{anime_name}/{episode_number}"
            
            logger.info(f"🔗 Novo URL: {new_url}")
            
            # Obtém novos links de streaming
            new_streaming_info = downloader.obter_links_streaming_episodio(new_url)
            
            if new_streaming_info['success'] and new_streaming_info['streaming_links']:
                # Atualiza os dados do vídeo
                self.video_data['streaming_links'] = new_streaming_info['streaming_links']
                
                # Recarrega as qualidades disponíveis
                self.quality_combo.clear()
                for quality in new_streaming_info['streaming_links'].keys():
                    self.quality_combo.addItem(quality)
                
                # Reproduz a mesma qualidade se disponível, senão a melhor disponível
                if self.current_quality in new_streaming_info['streaming_links']:
                    new_stream_url = new_streaming_info['streaming_links'][self.current_quality]
                else:
                    # Pega a primeira qualidade disponível
                    first_quality = list(new_streaming_info['streaming_links'].keys())[0]
                    new_stream_url = new_streaming_info['streaming_links'][first_quality]
                    self.current_quality = first_quality
                    self.quality_combo.setCurrentText(first_quality)
                
                # Reproduz o novo stream
                self.play_stream(new_stream_url)
                
                # Restaura a posição e estado de reprodução
                if was_playing:
                    QTimer.singleShot(2500, self.media_player.play)
                QTimer.singleShot(2000, lambda: self.media_player.setPosition(current_position))
                
            else:
                self.show_error("Não foi possível carregar o stream no idioma selecionado")
                
        except Exception as e:
            logger.error(f"❌ Erro ao alternar idioma: {e}")
            self.show_error(f"Erro ao alternar idioma: {str(e)}")
    
    def toggle_fullscreen(self):
        """Alterna entre tela cheia e normal"""
        if self.is_fullscreen:
            self.showNormal()
            self.fullscreen_btn.setText("⛶")
            # Garante que controles estejam visíveis ao sair da tela cheia
            self.show_controls()
            self.mouse_inactivity_timer.stop()
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("⛷")
            # Inicia timer para ocultar controles
            self.mouse_inactivity_timer.start(3000)
        self.is_fullscreen = not self.is_fullscreen
    
    def position_changed(self, position):
        """Atualiza quando a posição do vídeo muda"""
        try:
            if not self.progress_slider.isSliderDown():
                self.progress_slider.setValue(position)
            
            current_time = QTime(0, 0, 0, 0).addMSecs(position)
            self.current_time_label.setText(current_time.toString("mm:ss"))
        except Exception as e:
            pass  # Ignora erros temporários
    
    def duration_changed(self, duration):
        """Atualiza quando a duração do vídeo é conhecida"""
        try:
            if duration > 0:
                self.progress_slider.setRange(0, duration)
                total_time = QTime(0, 0, 0, 0).addMSecs(duration)
                self.total_time_label.setText(total_time.toString("mm:ss"))
        except Exception as e:
            pass  # Ignora erros temporários
    
    def playback_state_changed(self, state):
        """Atualiza o estado de reprodução"""
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸️")
            self.is_playing = True
        else:
            self.play_btn.setText("▶️")
            self.is_playing = False
    
    def update_controls(self):
        """Atualiza os controles periodicamente"""
        try:
            if (self.media_player and 
                self.media_player.playbackState() == QMediaPlayer.PlayingState and
                not self.progress_slider.isSliderDown()):
                
                position = self.media_player.position()
                duration = self.media_player.duration()
                
                if duration > 0:
                    self.progress_slider.setValue(position)
                    
        except Exception as e:
            pass  # Ignora erros de atualização
    
    def handle_player_error(self, error, error_string):
        """Lida com erros do player de forma robusta"""
        # Ignora erros menores durante transições
        if "demuxing" in error_string.lower() and not self.isActiveWindow():
            logger.debug(f"⚠️ Erro de demuxing ignorado (janela inativa): {error_string}")
            return
            
        if "smoke test" in error_string.lower() or "texture" in error_string.lower():
            logger.debug(f"⚠️ Erro gráfico ignorado: {error_string}")
            return
            
        error_messages = {
            QMediaPlayer.NoError: "Sem erro",
            QMediaPlayer.ResourceError: "Erro de recurso - possível problema de codec ou rede",
            QMediaPlayer.FormatError: "Erro de formato - arquivo incompatível", 
            QMediaPlayer.NetworkError: "Erro de rede - verifique sua conexão",
            QMediaPlayer.AccessDeniedError: "Acesso negado - problema de permissões"
        }
        
        error_msg = error_messages.get(error, f"Erro desconhecido: {error}")
        logger.error(f"❌ Erro no player: {error_msg} - {error_string}")
        
        # Só mostra dialog para erros críticos quando a janela está ativa
        if error not in [QMediaPlayer.NoError] and self.isActiveWindow():
            self.show_error(f"Erro na reprodução: {error_msg}")
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        QMessageBox.warning(self, "Erro no Player", message)
    
    def changeEvent(self, event):
        """Detecta quando a janela perde/ganha foco"""
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Janela minimizada - pausa a reprodução
                self.was_playing_before_minimize = self.is_playing
                if self.is_playing:
                    self.media_player.pause()
            else:
                # Janela restaurada - retoma se estava tocando
                if self.was_playing_before_minimize and not self.is_playing:
                    QTimer.singleShot(500, self.media_player.play)
        
        super().changeEvent(event)
    
    def closeEvent(self, event):
        """Limpeza ao fechar"""
        try:
            if self.update_timer:
                self.update_timer.stop()
            if self.mouse_inactivity_timer:
                self.mouse_inactivity_timer.stop()
            if self.media_player:
                self.media_player.stop()
        except Exception as e:
            logger.error(f"❌ Erro ao fechar player: {e}")
        
        event.accept()
    
    def keyPressEvent(self, event):
        """Atalhos de teclado"""
        if event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Left:
            self.rewind_10s()
        elif event.key() == Qt.Key_Right:
            self.forward_10s()
        elif event.key() == Qt.Key_Up:
            self.volume_slider.setValue(min(100, self.volume_slider.value() + 10))
        elif event.key() == Qt.Key_Down:
            self.volume_slider.setValue(max(0, self.volume_slider.value() - 10))
        elif event.key() == Qt.Key_F:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_M:
            self.toggle_mute()
        elif event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)