        title_layout = QHBoxLayout()

        # --- Icon label ---
        icon_label = QLabel()
        icon_pixmap = QPixmap(resource_path("assets/cat_working.png"))  # your image
        icon_pixmap = icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)  
        icon_label.setPixmap(icon_pixmap)

        # --- Text label ---
        title_text = QLabel("Select Apps to Allow")
        title_text.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_text.setAlignment(Qt.AlignCenter)

        # Add both into layout
        title_layout.addWidget(icon_label)
        title_layout.addWidget(title_text)
        title_layout.setAlignment(Qt.AlignCenter)  # centers both together

        # Add to your content layout
        content_layout.addLayout(title_layout)