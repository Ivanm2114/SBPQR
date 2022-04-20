import qrcode


def create_qr(string):
    data = string
    filename = "picture.png"
    img = qrcode.make(data)
    img.save(filename)
