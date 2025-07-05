import streamlit as st
import numpy as np
import cv2
from io import BytesIO
import time
st.set_page_config(page_title="Flag Pattern Blending", page_icon=":flag:", layout="wide")
st.title("Flag Pattern Blending Tool")
st.write("Upload a flag image and a pattern image to blend them together with natural folds. Are choose the pattern from below.")
from PIL import Image
# Upload inputs
flag_file = st.file_uploader("Upload the white flag image", type=["jpg", "jpeg", "png"])
pattern_file = st.file_uploader("Upload the pattern image", type=["jpg", "jpeg", "png"])
with st.spinner("Loading..."):
        time.sleep(5)
        st.success("Done!")
if flag_file and pattern_file:
    # Read files
    flag = np.array(Image.open(flag_file).convert("RGB"))[:, :, ::-1]  # RGB to BGR
    pattern = np.array(Image.open(pattern_file).convert("RGB"))[:, :, ::-1]

    # Resize pattern to match flag
    flag_h, flag_w = flag.shape[:2]
    pattern = cv2.resize(pattern, (flag_w, flag_h))

    # --- 2. Mesh warp pattern to simulate folds ---
    grid_size = 40
    grid_x, grid_y = np.meshgrid(np.linspace(0, flag_w, grid_size),
                                 np.linspace(0, flag_h, grid_size))
    
    displacement = (np.sin(grid_y / 15) + np.cos(grid_x / 25)) * 5
    dst_grid_x = grid_x.copy()
    dst_grid_y = grid_y + displacement

    map_x = cv2.resize(dst_grid_x.astype(np.float32), (flag_w, flag_h))
    map_y = cv2.resize(dst_grid_y.astype(np.float32), (flag_w, flag_h))

    warped_pattern = cv2.remap(pattern, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

    # --- 3. Create white cloth mask ---
    gray_flag = cv2.cvtColor(flag, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray_flag, 240, 255, cv2.THRESH_BINARY_INV)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    mask = cv2.GaussianBlur(mask, (25, 25), 0)
    alpha = mask.astype(np.float32) / 255.0
    alpha_3 = cv2.merge([alpha, alpha, alpha])

    # --- 4. Apply fold shading using luminance ---
    flag_lum = gray_flag.astype(np.float32) / 255.0
    pattern_f = warped_pattern.astype(np.float32) / 255.0
    fold_strength = 0.6

    for c in range(3):
        pattern_f[:, :, c] *= (flag_lum * fold_strength + (1 - fold_strength))

    # --- 5. Blend into flag ---
    flag_f = flag.astype(np.float32) / 255.0
    composite = pattern_f * alpha_3 + flag_f * (1 - alpha_3)
    composite = np.clip(composite * 255, 0, 255).astype(np.uint8)

    # Convert to RGB for Streamlit
    output_rgb = cv2.cvtColor(composite, cv2.COLOR_BGR2RGB)

    # --- 6. Show Results ---
    st.subheader("🖼️ Output: Pattern Mapped to Flag")
    st.image(output_rgb, use_column_width=True, caption="Result with folds and masking")

    # Download button
    img_pil = Image.fromarray(output_rgb)
    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG")
    byte_im = buf.getvalue()

    st.download_button("📥 Download Output.jpg", data=byte_im, file_name="Output.jpg", mime="image/jpeg")

else:
    st.info("👆 Upload both images above to get started.")

# Sidebar for instructions and examples
st.sidebar.title("Flag Pattern Blending Tool")
st.sidebar.write("This tool allows you to blend a pattern onto a flag image with natural folds. Upload your images to get started.")
# Display instructions
st.sidebar.header("Instructions")
st.sidebar.write("""
1. Upload a white flag image.
2. Upload a pattern image.
3. The tool will blend the pattern onto the flag with natural folds.
4. Download the blended output image.
""")
# Display example images
with st.sidebar:
    st.header("Example Images")
    st.write("You can use the following example images:")
    st.image("C:\\Users\\dhars\\OneDrive\\Pictures\\flag.jpg", caption="Example Flag", use_column_width=True)
    st.image("C:\\Users\\dhars\\OneDrive\\Pictures\\pattern.jpg", caption="Example Pattern", use_column_width=True)
    st.image("C:\\Users\\dhars\\OneDrive\\Pictures\\output_flag.jpg", caption="Example Output", use_column_width=True)
    st.write("You can also upload your own images.")

    with st.spinner("Loading..."):
        time.sleep(5)
    st.success("Done!")
st.sidebar.write("This tool is built using Streamlit, OpenCV, and PIL. Special thanks to the open-source community for their contributions!")
# Footer
st.sidebar.markdown("---")
st.sidebar.write("Made with ❤️ by [ Developer]")       
# Add a footer
st.sidebar.markdown("---")  
st.sidebar.write("© 2023 Flag Pattern Blending Tool")
# Add a link to the source code
st.sidebar.write("[View Source Code](https://github.com/yourusername/your-repo)")           
