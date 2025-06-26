# PokeXGames Helper

A sophisticated Pokemon battle assistant for PokeXGames with automated health management, Pokemon detection, and battle state recognition.

## Features

### Core Functionality
- **Automated Health Management**: Configurable health threshold with automatic healing
- **Area Selection**: 3 customizable screen areas for different game zones
- **Real-time Health Monitoring**: Live health percentage detection and display
- **Modern Interface**: Dark theme GUI with intuitive controls

### Advanced Features
- **Pokemon Detection**: Template-based Pokemon recognition system
- **Battle State Detection**: Automatic battle interface recognition
- **Image Comparison**: OpenCV-powered image matching with configurable thresholds
- **Multi-Monitor Support**: Works seamlessly across multiple displays
- **Debug Mode**: Comprehensive logging and debug image saving

## Quick Start

### Installation
1. Run `install.bat` to install dependencies automatically
2. Or manually install: `pip install -r requirements.txt`

### First Setup
1. Launch: `python pokexgames_helper.py`
2. Configure the Health Bar area (minimum requirement)
3. Optionally configure the 3 detection areas
4. Adjust settings as needed
5. Click "START HELPER"

## Configuration

### Health Management
- **Heal Key**: Keyboard key for healing (F1-F6, 1-3)
- **Health Threshold**: Percentage below which healing triggers
- **Auto Heal**: Enable/disable automatic healing

### Detection Settings
- **Match Threshold**: Image matching sensitivity (0.5-1.0)
- **Pokemon Detection**: Enable Pokemon template matching
- **Battle Detection**: Enable battle state recognition
- **Scan Interval**: How often to check health/status

### Areas
- **Health Bar**: Required - Pokemon health bar region
- **Area 1**: Optional - Custom detection zone
- **Area 2**: Optional - Custom detection zone  
- **Area 3**: Optional - Custom detection zone

## Templates

Place Pokemon template images in `assets/pokemon_templates/` as PNG files:
- `pikachu.png`
- `charizard.png`
- `etc.png`

The helper will automatically detect these Pokemon in the configured areas.

## Keyboard Shortcuts

- **F1-F6**: Configurable healing keys
- **ESC**: Cancel area selection
- All keys work while helper is running

## Logs and Debug

- **Activity Log**: Real-time helper status and actions
- **Debug Images**: Saved to `debug_images/` when debug mode enabled
- **Log Files**: Detailed logs saved to `logs/` directory

## Technical Details

### Requirements
- Python 3.7+
- Windows OS (for keyboard input)
- Dependencies: OpenCV, PIL, NumPy, pywin32

### Architecture
- **Modular Design**: Separate modules for detection, capture, input
- **Threading**: Non-blocking GUI with background helper thread
- **Error Handling**: Comprehensive error recovery and logging
- **Performance**: Optimized image processing and minimal resource usage

## Development

### Project Structure
```
pokexgames_helper/
├── app/
│   ├── config.py          # Configuration management
│   ├── gui.py             # Main interface
│   ├── core/              # Detection algorithms
│   ├── screen_capture/    # Area selection
│   └── utils/             # Helper functions
├── assets/                # Pokemon templates
├── logs/                  # Application logs
└── debug_images/          # Debug output
```

### Adding New Features
1. **Pokemon Templates**: Add PNG files to `assets/pokemon_templates/`
2. **Detection Logic**: Extend classes in `app/core/pokemon_detector.py`
3. **UI Elements**: Modify `app/gui.py` for interface changes
4. **Settings**: Update `app/config.py` for new configuration options

## Troubleshooting

### Common Issues
- **Health not detected**: Reconfigure health bar area, ensure good contrast
- **Helper not starting**: Check that health bar is configured
- **Key presses not working**: Run as administrator if needed
- **Detection inaccurate**: Adjust match threshold, add debug mode

### Debug Mode
Enable debug mode to:
- Save detection images for analysis
- View detailed logs
- Troubleshoot area selection issues
- Monitor health detection accuracy

## Support

For issues, feature requests, or contributions:
- Check logs in `logs/` directory
- Enable debug mode for detailed analysis
- Review debug images in `debug_images/`

## License

This project is for educational and personal use only.