from PIL import Image

img = Image.open("icon/verificar.png")
img.save("icon/icone.ico", format="ICO", sizes=[(16,16),(32,32),(48,48),(256,256)])
print("✅ icon/icone.ico criado!")