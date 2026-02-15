import fitz

doc = fitz.open("limitless-research-reports.pdf")
page = doc[0]
pix = page.get_pixmap(dpi=200)
pix.save("preview-cover.png")
print(f"✅ Preview saved: preview-cover.png ({pix.width}x{pix.height}px)")
