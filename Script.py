import cv2
import numpy as np

# ---------- 1. Load images ----------
flag = cv2.imread("C:\\Users\\dhars\\OneDrive\\Pictures\\flag.jpg")       # White flag with folds
pattern = cv2.imread("C:\\Users\\dhars\\OneDrive\\Pictures\\pattern.jpg") # Rectangular pattern to map

if flag is None or pattern is None:
    raise FileNotFoundError("❌ 'Flag.jpg' or 'Pattern.jpg' not found. Please check paths.")

# ---------- 2. Resize pattern to flag size ----------
flag_h, flag_w = flag.shape[:2]
pattern = cv2.resize(pattern, (flag_w, flag_h))

# ---------- 3. Simulate fabric flow with mesh warp ----------
# Create grid
grid_size = 40  # increase for smoother warping
grid_x, grid_y = np.meshgrid(np.linspace(0, flag_w, grid_size),
                             np.linspace(0, flag_h, grid_size))

# Apply vertical sine wave distortion (simulating folds)
displacement = (np.sin(grid_y / 15) + np.cos(grid_x / 25)) * 5  # adjust for fold depth
dst_grid_x = grid_x.copy()
dst_grid_y = grid_y + displacement

# Interpolate to full resolution
map_x = cv2.resize(dst_grid_x.astype(np.float32), (flag_w, flag_h))
map_y = cv2.resize(dst_grid_y.astype(np.float32), (flag_w, flag_h))

# Warp pattern image
warped_pattern = cv2.remap(pattern, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# ---------- 4. Create a mask for the white cloth (flag only) ----------
gray_flag = cv2.cvtColor(flag, cv2.COLOR_BGR2GRAY)
_, mask = cv2.threshold(gray_flag, 240, 255, cv2.THRESH_BINARY_INV)

# Clean and blur the mask for smooth edges
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
mask = cv2.GaussianBlur(mask, (25, 25), 0)
alpha = mask.astype(np.float32) / 255.0
alpha_3 = cv2.merge([alpha, alpha, alpha])

# ---------- 5. Apply fold shading using flag luminance ----------
flag_lum = gray_flag.astype(np.float32) / 255.0
pattern_f = warped_pattern.astype(np.float32) / 255.0
fold_strength = 0.6  # adjust to control how strong folds appear

for c in range(3):
    pattern_f[:, :, c] *= (flag_lum * fold_strength + (1 - fold_strength))

# ---------- 6. Blend the pattern only into the cloth region ----------
flag_f = flag.astype(np.float32) / 255.0
composite = pattern_f * alpha_3 + flag_f * (1 - alpha_3)
composite = np.clip(composite * 255, 0, 255).astype(np.uint8)

# ---------- 7. Save final result ----------
cv2.imwrite("Output.jpg", composite)
print("✅ Output saved as Output.jpg")
