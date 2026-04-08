#!/usr/bin/env python3
"""
Generate TrendLife icons for the extension
Based on Designer (2).png - TrendLife logo on gray gradient background
"""

from PIL import Image, ImageDraw
import os

def create_trendlife_icon(size):
    """Create a TrendLife icon with gray gradient background and red logo"""

    # Create image with gray gradient background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw gray gradient background with soft rounded corners
    # Top color: #B8BCC2, Bottom color: #7D8389
    for y in range(size):
        # Calculate gradient color
        ratio = y / size
        r = int(184 + (125 - 184) * ratio)  # 184 -> 125
        g = int(188 + (131 - 188) * ratio)  # 188 -> 131
        b = int(194 + (137 - 194) * ratio)  # 194 -> 137
        color = (r, g, b, 255)
        draw.line([(0, y), (size, y)], fill=color)

    # Create rounded corner mask (soft curves - 25% radius)
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = int(size * 0.25)  # 25% for soft curves
    mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=radius, fill=255)

    # Apply rounded corners
    img.putalpha(mask)

    # Draw TrendLife logo (two interlocking red ellipses)
    draw = ImageDraw.Draw(img)

    scale = size / 128  # Scale based on 128px reference
    centerX = size / 2
    centerY = size / 2

    # Red color
    red = (215, 25, 33, 255)  # #D71921

    # Left ellipse (smaller, filled, rotated -25 degrees)
    left_ellipse = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    left_draw = ImageDraw.Draw(left_ellipse)

    # Create filled ellipse
    rx1 = int(18 * scale)
    ry1 = int(22 * scale)
    x1 = int(centerX - 10 * scale)
    y1 = int(centerY)
    left_draw.ellipse([x1-rx1, y1-ry1, x1+rx1, y1+ry1], fill=red)

    # Rotate -25 degrees
    left_ellipse = left_ellipse.rotate(-25, expand=False, center=(centerX, centerY))
    img = Image.alpha_composite(img, left_ellipse)

    # Right ellipse (larger, hollow, rotated 15 degrees)
    right_ellipse = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    right_draw = ImageDraw.Draw(right_ellipse)

    # Create hollow ellipse (outline only)
    rx2 = int(26 * scale)
    ry2 = int(30 * scale)
    x2 = int(centerX + 8 * scale)
    y2 = int(centerY - 2 * scale)
    line_width = max(2, int(7 * scale))

    # Draw outer and inner ellipses to create hollow effect
    for i in range(line_width):
        right_draw.ellipse(
            [x2-rx2+i, y2-ry2+i, x2+rx2-i, y2+ry2-i],
            outline=red,
            width=1
        )

    # Rotate 15 degrees
    right_ellipse = right_ellipse.rotate(15, expand=False, center=(centerX, centerY))
    img = Image.alpha_composite(img, right_ellipse)

    return img

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Generate all icon sizes
    sizes = [16, 24, 32, 48, 128]

    for size in sizes:
        print(f"Generating icon{size}.png...")
        icon = create_trendlife_icon(size)

        # Save the icon
        output_path = os.path.join(script_dir, f'icon{size}.png')
        icon.save(output_path, 'PNG')
        print(f"✓ Saved: {output_path}")

    print("\n✓ All icons generated successfully!")
    print("Reload the extension in chrome://extensions to see the new icons.")

if __name__ == '__main__':
    main()
