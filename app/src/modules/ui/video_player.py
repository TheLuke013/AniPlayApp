# modules/ui/video_player.py
import os
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QComboBox, QFrame,
                               QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QUrl, QTimer, QTime
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
        self.current_language = 'legendado'  # ou 'dublado'
        
        self.setup_ui()
        self.setup_media_player()
        self.load_video()
        
    def setup_ui(self):
        self.setWindowTitle("Player de Anime")
        self.setMinimumSize(800, 500)  # 🔥 Tamanho mais razoável
        self.setStyleSheet("""
            QDialog {
                background: #000000;
                color: white;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Widget de vídeo com configurações de performance
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background: black;")
        self.video_widget.setAspectRatioMode(Qt.KeepAspectRatio)
        
        # 🔥 Otimizações de performance
        self.video_widget.setAttribute(Qt.WA_OpaquePaintEvent)
        self.video_widget.setAttribute(Qt.WA_NoSystemBackground)
        
        main_layout.addWidget(self.video_widget, 1)  # 🔥 O vídeo ocupa todo o espaço disponível
        
        # Controles
        controls_widget = self.create_controls()
        main_layout.addWidget(controls_widget)
        
        self.setLayout(main_layout)

    def play_stream(self, stream_url):
        """Reproduz um stream URL com tratamento de erros"""
        try:
            logger.info(f"🎬 Carregando stream: {stream_url[:100]}...")
            
            # Para qualquer reprodução anterior
            if self.media_player.playbackState() in [QMediaPlayer.PlayingState, QMediaPlayer.PausedState]:
                self.media_player.stop()
            
            # Limpa estado anterior
            self.media_player.setSource(QUrl())
            
            # Configura a fonte
            self.media_player.setSource(QUrl(stream_url))
            
            # 🔥 Aguarda um pouco antes de reproduzir para estabilizar
            QTimer.singleShot(100, self.start_playback)
            
            logger.info("✅ Stream configurado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar stream: {e}")
            self.show_error(f"Erro ao carregar vídeo: {str(e)}")

    def start_playback(self):
        """Inicia a reprodução após configuração"""
        try:
            self.media_player.play()
            logger.info("🎵 Reprodução iniciada")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar reprodução: {e}")
    
    def create_controls(self):
        controls = QFrame()
        controls.setMaximumHeight(80)  # 🔥 Limita a altura dos controles
        controls.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                padding: 8px;
                border-top: 1px solid #333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Barra de progresso
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMaximumHeight(15)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #333;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #ff7b00;
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
        self.progress_slider.sliderMoved.connect(self.seek_video)
        
        # Informações de tempo
        time_layout = QHBoxLayout()
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("color: #ccc; font-size: 11px;")
        self.current_time_label.setMaximumHeight(15)
        
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setStyleSheet("color: #ccc; font-size: 11px;")
        self.total_time_label.setMaximumHeight(15)
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        
        # Controles principais
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        # Botões com ícones menores
        self.play_btn = QPushButton("⏸️")
        self.play_btn.setFixedSize(32, 32)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #333;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        
        self.rewind_btn = QPushButton("⏪")
        self.rewind_btn.setFixedSize(32, 32)
        self.rewind_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #333;
            }
        """)
        self.rewind_btn.clicked.connect(self.rewind_10s)
        self.rewind_btn.setToolTip("Voltar 10 segundos")
        
        self.forward_btn = QPushButton("⏩")
        self.forward_btn.setFixedSize(32, 32)
        self.forward_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #333;
            }
        """)
        self.forward_btn.clicked.connect(self.forward_10s)
        self.forward_btn.setToolTip("Avançar 10 segundos")
        
        # Seletor de qualidade mais compacto
        self.quality_combo = QComboBox()
        self.quality_combo.setMaximumHeight(28)
        self.quality_combo.setMaximumWidth(120)
        self.quality_combo.setStyleSheet("""
            QComboBox {
                background: #333;
                color: white;
                border: 1px solid #555;
                padding: 2px 5px;
                border-radius: 3px;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 15px;
            }
        """)
        self.quality_combo.currentTextChanged.connect(self.change_quality)
        
        # Botão de idioma mais compacto
        self.language_btn = QPushButton("🇧🇷 Leg")
        self.language_btn.setMaximumHeight(28)
        self.language_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
            }
        """)
        self.language_btn.clicked.connect(self.toggle_language)
        self.language_btn.setToolTip("Alternar entre legendado e dublado")
        
        # Botão tela cheia
        self.fullscreen_btn = QPushButton("⛶")
        self.fullscreen_btn.setFixedSize(32, 32)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background: #333;
            }
        """)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_btn.setToolTip("Tela cheia (F)")
        
        # Adiciona os controles
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.rewind_btn)
        controls_layout.addWidget(self.forward_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(QLabel("Qual:"))
        controls_layout.addWidget(self.quality_combo)
        controls_layout.addWidget(self.language_btn)
        controls_layout.addWidget(self.fullscreen_btn)
        
        layout.addWidget(self.progress_slider)
        layout.addLayout(time_layout)
        layout.addLayout(controls_layout)
        
        controls.setLayout(layout)
        return controls

    # No método setup_media_player do VideoPlayerDialog
    def setup_media_player(self):
        """Configura o player de mídia"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # 🔥 CRÍTICO: Desativa aceleração de hardware para evitar congelamentos
        # Isso resolve os erros D3D11 e de textura
        self.media_player.setProperty("videoOutput", "software")
        
        # Conecta sinais
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.playback_state_changed)
        self.media_player.errorOccurred.connect(self.handle_player_error)

    def load_video(self):
        """Carrega o vídeo baseado nos dados fornecidos"""
        streaming_links = self.video_data.get('streaming_links', {})
        
        if not streaming_links:
            self.show_error("Nenhum link de streaming disponível")
            return
        
        # Preenche o seletor de qualidade
        self.quality_combo.clear()
        for quality in streaming_links.keys():
            self.quality_combo.addItem(quality)
        
        # Tenta carregar a melhor qualidade primeiro
        preferred_qualities = ['1080p', '720p', '480p', '360p', 'auto', 'direct']
        for quality in preferred_qualities:
            if quality in streaming_links:
                self.current_quality = quality
                self.quality_combo.setCurrentText(quality)
                self.play_stream(streaming_links[quality])
                break
        
        if not self.current_quality:
            # Usa o primeiro link disponível
            first_quality = list(streaming_links.keys())[0]
            self.current_quality = first_quality
            self.quality_combo.setCurrentText(first_quality)
            self.play_stream(streaming_links[first_quality])
    
    def toggle_play_pause(self):
        """Alterna entre play e pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶️")
        else:
            self.media_player.play()
            self.play_btn.setText("⏸️")
    
    def rewind_10s(self):
        """Volta 10 segundos"""
        current_pos = self.media_player.position()
        self.media_player.setPosition(max(0, current_pos - 10000))
    
    def forward_10s(self):
        """Avança 10 segundos"""
        current_pos = self.media_player.position()
        duration = self.media_player.duration()
        self.media_player.setPosition(min(duration, current_pos + 10000))
    
    def seek_video(self, position):
        """Busca uma posição específica no vídeo"""
        self.media_player.setPosition(position)
    
    def change_quality(self, quality):
        """Muda a qualidade do vídeo"""
        if quality != self.current_quality:
            streaming_links = self.video_data.get('streaming_links', {})
            if quality in streaming_links:
                self.current_quality = quality
                current_position = self.media_player.position()
                self.play_stream(streaming_links[quality])
                # Restaura a posição após carregar o novo stream
                QTimer.singleShot(1000, lambda: self.media_player.setPosition(current_position))
    
    def toggle_language(self):
        """Alterna entre legendado e dublado"""
        if self.current_language == 'legendado':
            self.current_language = 'dublado'
            self.language_btn.setText("🇧🇷 Dublado")
            # Aqui você implementaria a lógica para trocar o áudio
        else:
            self.current_language = 'legendado'
            self.language_btn.setText("🇧🇷 Legendado")
            # Aqui você implementaria a lógica para trocar o áudio
    
    def toggle_fullscreen(self):
        """Alterna entre tela cheia e normal"""
        if self.is_fullscreen:
            self.showNormal()
            self.fullscreen_btn.setText("⛶")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("⛷")
        self.is_fullscreen = not self.is_fullscreen
    
    def position_changed(self, position):
        """Atualiza a barra de progresso quando a posição muda"""
        try:
            # Evita atualizações muito frequentes
            if not self.progress_slider.isSliderDown():
                self.progress_slider.setValue(position)
            
            # Atualiza o tempo atual
            current_time = QTime(0, 0, 0, 0)
            current_time = current_time.addMSecs(position)
            self.current_time_label.setText(current_time.toString("mm:ss"))
        except Exception as e:
            logger.debug(f"Erro em position_changed: {e}")

    def duration_changed(self, duration):
        """Atualiza a duração total do vídeo"""
        try:
            if duration > 0:
                self.progress_slider.setRange(0, duration)
                
                total_time = QTime(0, 0, 0, 0)
                total_time = total_time.addMSecs(duration)
                self.total_time_label.setText(total_time.toString("mm:ss"))
        except Exception as e:
            logger.debug(f"Erro em duration_changed: {e}")

    def seek_video(self, position):
        """Busca uma posição específica no vídeo"""
        try:
            # Só busca se o vídeo estiver carregado
            if self.media_player.duration() > 0:
                self.media_player.setPosition(position)
        except Exception as e:
            logger.debug(f"Erro em seek_video: {e}")
    
    def duration_changed(self, duration):
        """Atualiza a duração total do vídeo"""
        self.progress_slider.setRange(0, duration)
        
        total_time = QTime(0, 0, 0, 0)
        total_time = total_time.addMSecs(duration)
        self.total_time_label.setText(total_time.toString("mm:ss"))
    
    def playback_state_changed(self, state):
        """Atualiza o estado de reprodução"""
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸️")
            self.is_playing = True
        else:
            self.play_btn.setText("▶️")
            self.is_playing = False
    
    def handle_player_error(self, error, error_string):
        """Lida com erros do player de forma mais específica"""
        # 🔥 Ignora erros menores ou repetidos
        if "smoke test" in error_string.lower() or "texture" in error_string.lower():
            logger.debug(f"⚠️ Erro gráfico ignorado: {error_string}")
            return
            
        error_messages = {
            QMediaPlayer.NoError: "Sem erro",
            QMediaPlayer.ResourceError: "Erro de recurso - possível problema de codec",
            QMediaPlayer.FormatError: "Erro de formato - arquivo corrompido ou incompatível", 
            QMediaPlayer.NetworkError: "Erro de rede - problema de conexão",
            QMediaPlayer.AccessDeniedError: "Acesso negado - permissões ou CORS"
        }
        
        error_msg = error_messages.get(error, f"Erro desconhecido: {error}")
        logger.error(f"❌ Erro no player ({error}): {error_msg} - {error_string}")
        
        # Só mostra dialog para erros críticos
        if error not in [QMediaPlayer.NoError]:
            self.show_error(f"Erro na reprodução: {error_msg}")
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        QMessageBox.warning(self, "Erro no Player", message)
    
    def resizeEvent(self, event):
        """Redimensiona o overlay de loading quando a janela muda de tamanho"""
        super().resizeEvent(event)
        # Mantém o loading overlay do tamanho do video widget
        if hasattr(self, 'loading_overlay'):
            self.loading_overlay.setGeometry(self.video_widget.rect())

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Left:
            self.rewind_10s()
        elif event.key() == Qt.Key_Right:
            self.forward_10s()
        elif event.key() == Qt.Key_F:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self.is_fullscreen:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)