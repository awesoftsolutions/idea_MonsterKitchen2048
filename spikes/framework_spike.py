"""Framework spike: 700x800 window, blue placeholder rect, Escape/close handling, screenshot capture."""

# CHANGELOG:
# - Sprint 1: Created framework spike — pygame 700x800 window with blue placeholder rect, event handling, and screenshot capture
import os
import sys
import pygame

WINDOW_WIDTH, WINDOW_HEIGHT = 700, 800
WINDOW_TITLE = "Favur 2048"
BACKGROUND_COLOR = (30, 30, 30)
RECT_COLOR = (0, 120, 215)
RECT_SIZE = 100
RECT_X = (WINDOW_WIDTH - RECT_SIZE) // 2
RECT_Y = (WINDOW_HEIGHT - RECT_SIZE) // 2
SCREENSHOT_PATH = "visual-proof/framework_spike.png"
FPS = 10

# E-SPIKE-02: ensure screenshot directory exists before save
os.makedirs("visual-proof", exist_ok=True)

# E-SPIKE-01: initialize pygame with failure handling
try:
    init_result = pygame.init()
    if init_result[1] > 0:
        print("pygame.init() failed", file=sys.stderr)
        sys.exit(1)
except Exception as e:
    print(f"Failed to initialize pygame: {e}", file=sys.stderr)
    sys.exit(1)

# Create the display window
try:
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
except Exception as e:
    print(f"Failed to create window: {e}", file=sys.stderr)
    pygame.quit()
    sys.exit(1)

clock = pygame.time.Clock()
running = True

# Main event loop — Clock.tick(10) for responsive close handling
frame_count = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            running = False
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, RECT_COLOR, (RECT_X, RECT_Y, RECT_SIZE, RECT_SIZE))
    pygame.display.flip()
    clock.tick(FPS)
    frame_count += 1
    if frame_count >= 3:
        running = False

# IF-003: capture screenshot BEFORE pygame.quit()
try:
    pygame.image.save(screen, SCREENSHOT_PATH)
    print(f"Screenshot saved to {SCREENSHOT_PATH}")
except Exception as e:
    print(f"Failed to save screenshot: {e}", file=sys.stderr)
    pygame.quit()
    sys.exit(1)

pygame.quit()
print("Framework spike completed successfully")
