#import <Cocoa/Cocoa.h>

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc < 2) return 1;
        NSImage *image = [[NSImage alloc] initWithSize:NSMakeSize(1024, 1024)];
        [image lockFocus];
        [[NSColor colorWithSRGBRed:0.10 green:0.15 blue:0.22 alpha:1] setFill];
        [[NSBezierPath bezierPathWithRoundedRect:NSMakeRect(24, 24, 976, 976) xRadius:220 yRadius:220] fill];
        NSString *title = @"FA";
        NSDictionary *attributes = @{
            NSFontAttributeName: [NSFont systemFontOfSize:360 weight:NSFontWeightBold],
            NSForegroundColorAttributeName: NSColor.whiteColor,
            NSKernAttributeName: @-28
        };
        NSSize textSize = [title sizeWithAttributes:attributes];
        [title drawAtPoint:NSMakePoint((1024 - textSize.width) / 2 - 10, (1024 - textSize.height) / 2 + 20) withAttributes:attributes];
        [[NSColor colorWithSRGBRed:0.92 green:0.52 blue:0.30 alpha:1] setFill];
        NSBezierPath *star = [NSBezierPath bezierPath];
        for (NSUInteger i = 0; i < 8; i++) {
            double angle = (double)i * M_PI / 4 - M_PI / 2;
            double radius = i % 2 == 0 ? 83 : 33;
            NSPoint point = NSMakePoint(797 + cos(angle) * radius, 782 + sin(angle) * radius);
            if (i == 0) [star moveToPoint:point]; else [star lineToPoint:point];
        }
        [star closePath];
        [star fill];
        [image unlockFocus];
        NSBitmapImageRep *bitmap = [NSBitmapImageRep imageRepWithData:image.TIFFRepresentation];
        NSData *png = [bitmap representationUsingType:NSBitmapImageFileTypePNG properties:@{}];
        return [png writeToFile:[NSString stringWithUTF8String:argv[1]] atomically:YES] ? 0 : 1;
    }
}
