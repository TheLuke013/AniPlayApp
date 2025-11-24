from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QSlider, QWidget, QFrame, 
                               QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QUrl, QTime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QIcon, QFont
import json
from loguru import logger

class VideoPlayerDialog(QDialog):
    def __init__(self, video_data, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.video_url = video_data.get('video_url')
        self.episode_data = video_data.get('episode_data')
        self.subtitles = video_data.get('subtitles', [])
        self.intro = video_data.get('intro', {})
        self.outro = video_data.get('outro', {})
        self.headers = video_data.get('headers', {})
        
        # Controle de reprodução
        self.is_playing = False
        self.current_position = 0
        self.video_duration = 0
        
        self.setup_ui()
        self.setup_media_player()
        
    def setup_ui(self):
        self.setWindowTitle(f"AniPlay - {self.episode_data.get('title', 'Player')}")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QDialog {
                background: #1a1a1a;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header com informações do episódio
        header = self.create_header()
        layout.addWidget(header)
        
        # Widget de vídeo
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("""
            QVideoWidget {
                background: #000000;
                border: none;
            }
        """)
        layout.addWidget(self.video_widget)
        
        # Controles do player
        controls = self.create_controls()
        layout.addWidget(controls)
        
        self.setLayout(layout)
    
    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                border-bottom: 2px solid #ff7b00;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Informações do episódio
        episode_info = QLabel(f"{self.episode_data.get('title', 'Episódio')}")
        episode_info.setStyleSheet("""
            QLabel {
                color: #ff7b00;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        # Botão fechar
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ff4444;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff6666;
            }
        """)
        close_btn.clicked.connect(self.close_player)
        
        layout.addWidget(episode_info)
        layout.addStretch()
        layout.addWidget(close_btn)
        
        header.setLayout(layout)
        return header
    
    def create_controls(self):
        controls = QWidget()
        controls.setFixedHeight(80)
        controls.setStyleSheet("""
            QWidget {
                background: #2a2a2a;
                border-top: 1px solid #444;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(8)
        
        # Barra de progresso
        progress_layout = QHBoxLayout()
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #888; font-size: 12px;")
        self.time_label.setFixedWidth(100)
        
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #444;
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
            QSlider::handle:horizontal:hover {
                background: #ff9500;
                width: 14px;
                height: 14px;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #ff7b00;
                border-radius: 2px;
            }
        """)
        self.progress_slider.sliderMoved.connect(self.seek_video)
        self.progress_slider.sliderPressed.connect(self.pause_video)
        self.progress_slider.sliderReleased.connect(self.play_video)
        
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.progress_slider)
        
        # Botões de controle
        buttons_layout = QHBoxLayout()
        
        # Botão play/pause
        self.play_btn = QPushButton("⏸️")
        self.play_btn.setFixedSize(50, 40)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #ff7b00;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #ff9500;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        
        # Botão voltar 10s
        rewind_btn = QPushButton("⏪ 10s")
        rewind_btn.setFixedSize(80, 40)
        rewind_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        rewind_btn.clicked.connect(self.rewind_10s)
        
        # Botão avançar 10s
        forward_btn = QPushButton("⏩ 10s")
        forward_btn.setFixedSize(80, 40)
        forward_btn.setStyleSheet(rewind_btn.styleSheet())
        forward_btn.clicked.connect(self.forward_10s)
        
        # Botão pular intro/outro
        self.skip_btn = QPushButton("⏭️ Pular")
        self.skip_btn.setFixedSize(80, 40)
        self.skip_btn.setStyleSheet(rewind_btn.styleSheet())
        self.skip_btn.clicked.connect(self.skip_section)
        self.skip_btn.hide()  # Inicialmente escondido
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(5)
        
        volume_icon = QLabel("🔊")
        volume_icon.setStyleSheet("color: #888;")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setStyleSheet(self.progress_slider.styleSheet())
        self.volume_slider.valueChanged.connect(self.set_volume)
        
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(rewind_btn)
        buttons_layout.addWidget(forward_btn)
        buttons_layout.addWidget(self.skip_btn)
        buttons_layout.addStretch()
        buttons_layout.addLayout(volume_layout)
        
        layout.addLayout(progress_layout)
        layout.addLayout(buttons_layout)
        
        controls.setLayout(layout)
        return controls
    
    def setup_media_player(self):
        """Configura o media player"""
        try:
            # Cria o player de mídia
            self.media_player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.media_player.setAudioOutput(self.audio_output)
            self.media_player.setVideoOutput(self.video_widget)
            
            # Configura a URL do vídeo
            video_url = QUrl(self.video_url)
            self.media_player.setSource(video_url)
            
            # Conecta os sinais
            self.media_player.durationChanged.connect(self.on_duration_changed)
            self.media_player.positionChanged.connect(self.on_position_changed)
            self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
            self.media_player.errorOccurred.connect(self.on_player_error)
            
            # Configura volume inicial
            self.audio_output.setVolume(self.volume_slider.value() / 100)
            
            # Timer para verificar seções pular (intro/outro)
            self.skip_timer = QTimer()
            self.skip_timer.timeout.connect(self.check_skip_sections)
            self.skip_timer.start(1000)  # Verifica a cada segundo
            
            logger.info("✅ Player de mídia configurado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar player: {e}")
            self.show_error("Erro ao configurar o player de vídeo")
    
    def toggle_play_pause(self):
        """Alterna entre play e pause"""
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.pause_video()
        else:
            self.play_video()
    
    def play_video(self):
        """Inicia a reprodução"""
        self.media_player.play()
        self.play_btn.setText("⏸️")
        self.is_playing = True
    
    def pause_video(self):
        """Pausa a reprodução"""
        self.media_player.pause()
        self.play_btn.setText("▶️")
        self.is_playing = False
    
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
    
    def set_volume(self, value):
        """Define o volume"""
        self.audio_output.setVolume(value / 100)
    
    def skip_section(self):
        """Pula a seção atual (intro/outro)"""
        current_pos = self.media_player.position() / 1000  # Converter para segundos
        
        # Verifica se está na intro
        intro_start = self.intro.get('start', 0)
        intro_end = self.intro.get('end', 0)
        if intro_start <= current_pos <= intro_end and intro_end > 0:
            self.media_player.setPosition(intro_end * 1000)
            return
        
        # Verifica se está no outro
        outro_start = self.outro.get('start', 0)
        outro_end = self.outro.get('end', 0)
        if outro_start <= current_pos <= outro_end and outro_end > 0:
            self.media_player.setPosition(outro_end * 1000)
            return
    
    def check_skip_sections(self):
        """Verifica se deve mostrar o botão de pular"""
        if not self.is_playing:
            return
            
        current_pos = self.media_player.position() / 1000  # Converter para segundos
        
        # Verifica intro
        intro_start = self.intro.get('start', 0)
        intro_end = self.intro.get('end', 0)
        if intro_start <= current_pos <= intro_end and intro_end > 0:
            self.skip_btn.setText("⏭️ Pular Intro")
            self.skip_btn.show()
            return
        
        # Verifica outro
        outro_start = self.outro.get('start', 0)
        outro_end = self.outro.get('end', 0)
        if outro_start <= current_pos <= outro_end and outro_end > 0:
            self.skip_btn.setText("⏭️ Pular Outro")
            self.skip_btn.show()
            return
        
        self.skip_btn.hide()
    
    def on_duration_changed(self, duration):
        """Quando a duração do vídeo é carregada"""
        self.video_duration = duration
        self.progress_slider.setRange(0, duration)
        self.update_time_label()
    
    def on_position_changed(self, position):
        """Quando a posição do vídeo muda"""
        self.current_position = position
        self.progress_slider.setValue(position)
        self.update_time_label()
        
        # Salva o progresso a cada 10 segundos
        if position % 10000 < 100:  # Aproximadamente a cada 10s
            self.save_watch_progress()
    
    def on_playback_state_changed(self, state):
        """Quando o estado de reprodução muda"""
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("⏸️")
            self.is_playing = True
        else:
            self.play_btn.setText("▶️")
            self.is_playing = False
    
    def update_time_label(self):
        """Atualiza o label de tempo"""
        current_time = QTime(0, 0).addMSecs(self.current_position)
        total_time = QTime(0, 0).addMSecs(self.video_duration)
        
        current_str = current_time.toString("mm:ss")
        total_str = total_time.toString("mm:ss")
        
        self.time_label.setText(f"{current_str} / {total_str}")
    
    def save_watch_progress(self):
        """Salva o progresso de assistir"""
        try:
            progress_data = {
                'episode_id': self.episode_data.get('episodeId'),
                'episode_number': self.episode_data.get('number'),
                'anime_id': self.episode_data.get('anime_id', self.video_data.get('anilistID')),
                'position': self.current_position,
                'duration': self.video_duration,
                'timestamp': QTime.currentTime().toString("hh:mm:ss")
            }
            
            # Aqui você pode salvar no banco de dados do usuário
            logger.info(f"💾 Progresso salvo: {self.current_position}/{self.video_duration}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar progresso: {e}")
    
    def on_player_error(self, error, error_string):
        """Trata erros do player"""
        logger.error(f"❌ Erro no player: {error_string}")
        self.show_error(f"Erro na reprodução: {error_string}")
    
    def show_error(self, message):
        """Mostra mensagem de erro"""
        QMessageBox.critical(self, "Erro no Player", message)
    
    def close_player(self):
        """Fecha o player e salva o progresso final"""
        self.save_watch_progress()
        self.media_player.stop()
        self.accept()
    
    def closeEvent(self, event):
        """Quando o player é fechado"""
        self.close_player()
        event.accept()