# SnapMosaic - Development Roadmap

This document outlines the planned features and improvements for SnapMosaic.

---

## 🚀 Version 2.0.0 - First Public Release (Current Priority)

**Target:** Q4 2024 / Q1 2025

### Critical Pre-Release Items

- [x] **Clear All Confirmation Dialog** ✅ COMPLETED
  - Add confirmation dialog before clearing all captures
  - Option to "Don't ask again" with persistence in config
  - Priority: **HIGH** - Prevents accidental data loss
  - Estimated: 30 minutes

- [x] **Keyboard Shortcuts Enhancement** ✅ COMPLETED
  - `Ctrl+S` - Quick save selected/last image ✅ COMPLETED
  - `Delete` key - Delete selected/hovered image ✅ COMPLETED
  - `Ctrl+C` - Copy selected/hovered image to clipboard ✅ COMPLETED
  - `Escape` - Stop auto-snap mode if running ✅ COMPLETED
  - Display shortcuts in tooltips/status bar ✅ COMPLETED
  - Priority: **HIGH** - Significantly improves UX
  - Estimated: 2-3 hours

- [x] **Visual Feedback for Auto-Snap** ✅ COMPLETED
  - Brief visual indicator when capture occurs in auto-snap mode
  - Optional capture counter in status bar or button tooltip
  - Helps user confirm automation is working
  - Priority: **MEDIUM** - Improves confidence in automation
  - Estimated: 1 hour

- [x] **Settings - Reset Confirmations** ✅ COMPLETED
  - Button in General settings to re-enable all confirmation dialogs
  - Priority: **HIGH** - Complements "Don't ask again" feature
  - Estimated: 15 minutes

- [ ] **Platform Testing**
  - [ ] Windows (Primary)
  - [ ] macOS
  - [ ] Linux (Ubuntu/Fedora)
  - Verify hotkeys, system tray, High-DPI on each platform
  - Priority: **HIGH**
  - Estimated: 4-6 hours

- [ ] **Documentation Polish**
  - Review and update all documentation for new features
  - Create simple video/GIF demo for README
  - Add troubleshooting section
  - Priority: **MEDIUM**
  - Estimated: 2 hours

---

## 📋 Version 2.10.0 - Quick Wins (Post-Release)

**Target:** 1-2 months after v2.0.0

### Quality of Life Improvements

- [ ] **Export All Functionality**
  - "Save All" button to export all current captures to folder
  - Batch naming with automatic numbering/timestamps
  - Progress indicator for large batches
  - Estimated: 3-4 hours

- [ ] **Image Selection System**
  - Click to select an image (highlight border)
  - Multi-select with Ctrl+Click
  - Keyboard navigation (arrow keys)
  - Enables better keyboard shortcut support
  - Estimated: 4-5 hours

- [ ] **Undo Delete Operation**
  - Single-level undo for accidental deletes
  - "Undo" notification toast/snackbar
  - Clears on next capture or manual clear
  - Estimated: 2-3 hours

- [ ] **Capture Status Indicator**
  - Small status bar showing:
    - Number of captures in grid
    - Auto-snap status and next capture time
    - Last action performed
  - Estimated: 2 hours

- [ ] **Window Always-on-Top Option**
  - Toggle in settings to keep window above others
  - Useful when capturing from other applications
  - Estimated: 30 minutes

---

## 🎨 Version 2.20.0 - Enhanced Viewing

**Target:** 3-4 months after v2.0.0

### Image Viewing Enhancements

- [ ] **Full-Screen Image Viewer**
  - Double-click image to view full-screen
  - Navigate with arrow keys
  - Zoom controls
  - Quick copy/save actions
  - Estimated: 6-8 hours

- [ ] **Comparison Mode**
  - Select two images for side-by-side comparison
  - Synchronized zoom/pan
  - Diff highlighting option
  - Perfect for QA and UI comparison use cases
  - Estimated: 8-10 hours

- [ ] **Image Filtering and Sorting**
  - Sort by capture time, size, saved status
  - Filter saved/unsaved images
  - Search by timestamp
  - Estimated: 4-5 hours

- [ ] **Grid Layout Customization**
  - User-configurable thumbnail size
  - List view option
  - Compact mode
  - Estimated: 3-4 hours

---

## 🔧 Version 2.30.0 - Advanced Features

**Target:** 6 months after v2.0.0

### Power User Features

- [ ] **Basic Image Annotations**
  - Add arrows, rectangles, highlights before saving
  - Text annotations
  - Simple drawing tools
  - Non-destructive (annotations as layer)
  - Estimated: 15-20 hours

- [ ] **Smart Capture Modes**
  - **Change Detection**: Only capture when region content changes
  - **Motion Detection**: Capture when movement detected
  - **Smart Intervals**: Vary interval based on activity
  - Useful for monitoring workflows
  - Estimated: 10-12 hours

- [ ] **Capture Profiles**
  - Save multiple region/settings combinations
  - Quick-switch between profiles
  - Import/export profiles
  - Estimated: 5-6 hours

- [ ] **GIF/Video Export**
  - Create animated GIF from capture sequence
  - Time-lapse video export
  - Configurable framerate and quality
  - Estimated: 8-10 hours

---

## 🌐 Version 3.0.0 - Collaboration Features

**Target:** 1 year after v2.0.0

### Sharing and Integration

- [ ] **OCR Integration**
  - Extract text from captures
  - Copy text to clipboard
  - Search captures by contained text
  - Requires OCR library integration (tesseract)
  - Estimated: 12-15 hours

- [ ] **Cloud Upload Integration**
  - Direct upload to Imgur, Dropbox, Google Drive
  - Shareable links
  - Automatic clipboard copy of link
  - Estimated: 15-20 hours

- [ ] **Capture History and Sessions**
  - Persistent capture history across sessions
  - Session management (save/load capture sets)
  - Export session as project
  - Estimated: 10-12 hours

- [ ] **Plugin System**
  - Allow community extensions
  - Custom post-processing filters
  - Integration with external tools
  - Estimated: 20-25 hours

---

## 🎯 Ongoing Improvements

These items are continuously evaluated and implemented as needed:

### Performance
- [ ] Optimize grid redraw performance for 100+ images
- [ ] Lazy loading for large capture sets
- [ ] Memory usage optimization for long sessions

### Platform-Specific
- [ ] Native file dialogs
- [ ] Platform-specific icon themes
- [ ] macOS menu bar integration
- [ ] Linux desktop environment integration

### Accessibility
- [ ] Screen reader support
- [ ] High contrast theme
- [ ] Keyboard-only navigation
- [ ] Configurable UI scaling

### Localization
- [ ] i18n framework implementation
- [ ] Spanish translation
- [ ] French translation
- [ ] German translation
- [ ] Community translation contributions

---

## 🐛 Known Issues / Technical Debt

Items to address as priority allows:

- [ ] System tray behavior on some Linux desktop environments
- [ ] Hotkey conflicts with certain applications
- [ ] Very large region captures (>4K) performance
- [ ] Rare edge case with multi-monitor DPI scaling differences

---

## 💡 Community Requested Features

Features will be added here based on user feedback after release:

- *Awaiting community input*

---

## Version Strategy

- **Major versions (X.0.0)**: Significant new functionality or breaking changes
- **Minor versions (2.X.0)**: New features, non-breaking improvements
- **Patch versions (2.1.X)**: Bug fixes, minor tweaks

---

## Contributing

We welcome contributions! Please see:
- Feature requests: Open an issue with the `feature-request` label
- Bug reports: Open an issue with the `bug` label
- Pull requests: See CONTRIBUTING.md (to be created)

---

**Last Updated:** 2025-10-27  
**Current Version:** 2.0.0 (first stable release)  
**Next Milestone:** v2.10.0
