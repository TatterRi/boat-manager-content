import AppKit
let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
let ptH: CGFloat = 64, ptW = ptH * 589.84 / 556.85
for s in [1, 2, 3] {
    let w = Int((ptW * CGFloat(s)).rounded()), h = Int((ptH * CGFloat(s)).rounded())
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    img.draw(in: NSRect(x: 0, y: 0, width: w, height: h))
    NSGraphicsContext.restoreGraphicsState()
    let name = s == 1 ? "United_States_Coast_Guard.png" : "United_States_Coast_Guard@\(s)x.png"
    try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: CommandLine.arguments[2] + "/" + name))
}
