#!/usr/bin/env python3
"""
snatch - Generate presentable images of code snippets from the terminal
Uses Playwright (Chromium) for perfect HTML/CSS rendering
"""

import sys
import argparse
import asyncio

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright is not installed.", file=sys.stderr)
    print("Install with:", file=sys.stderr)
    print("  pip install playwright", file=sys.stderr)
    print("  playwright install chromium", file=sys.stderr)
    sys.exit(1)

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer, get_lexer_for_filename
    from pygments.formatters import HtmlFormatter
    from pygments.styles import get_style_by_name, get_all_styles
except ImportError:
    print("Error: pygments is not installed.", file=sys.stderr)
    print("Install with: pip install pygments", file=sys.stderr)
    sys.exit(1)


def lighten_color(hex_color, amount=0.2):
    """Lighten a hex color by a given amount"""
    # Remove '#' if present
    hex_color = hex_color.lstrip("#")

    # Convert to RGB
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    # Lighten
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))

    return f"#{r:02x}{g:02x}{b:02x}"


def darken_color(hex_color, amount=0.3):
    """Darken a hex color by a given amount"""
    # Remove '#' if present
    hex_color = hex_color.lstrip("#")

    # Convert to RGB
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    # Darken
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))

    return f"#{r:02x}{g:02x}{b:02x}"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: radial-gradient(ellipse at center, {gradient_start} 0%, {gradient_end} 100%);
            padding: {margin}px;
            display: inline-block;
            -webkit-font-smoothing: antialiased;
        }}
        
        .window {{
            background: {bg_color};
            border-radius: 8px;
            overflow: hidden;
            display: inline-block;
            box-shadow: 0 20px 68px rgba(0, 0, 0, 0.55);
        }}
        
        .window-header-chrome {{
            background: {window};
            height: 35px;
            display: flex;
            align-items: center;
            padding-left: 12px;
            gap: 6px;
        }}

        .window-header-clear {{
            background: {bg_color};
            height: 35px;
            display: flex;
            align-items: center;
            padding-left: 12px;
            gap: 6px;
            margin-bottom: -0.5em;
        }}
        
        .window-button {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }}
        
        .window-button.red {{ background: #ff5f56; }}
        .window-button.yellow {{ background: #ffbd2e; }}
        .window-button.green {{ background: #27c93f; }}
        
        .code-container {{
            background: {bg_color};
            padding: {padding}px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'Courier New', monospace;
            font-size: {font_size}px;
            line-height: 1.5;
            overflow-x: auto;

            /* Crisp text rendering */
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: geometricPrecision;
            font-smooth: never;
            image-rendering: crisp-edges;
        }}
        
        .highlight pre {{
            margin: 0;
            padding: 0;
        }}
        
        /* Aggressively override ALL backgrounds to match */
        .highlight,
        .highlight *,
        .highlighttable,
        .highlighttable * {{
            background-color: {bg_color} !important;
            background: {bg_color} !important;
            border: none !important;
        }}
        
        .highlight .linenos {{
            padding-right: 0.5em !important;
            user-select: none;
            text-align: right;
        }}
        
        {pygments_css}
    </style>
</head>
<body>
    <div class="window">
        {window_header}
        <div class="code-container">
            {highlighted_code}
        </div>
    </div>
</body>
</html>
"""


async def create_code_image(
    code,
    style="monokai",
    font_size=14,
    padding=40,
    show_line_numbers=True,
    output="code.png",
    show_window=True,
    show_decorations=True,
    language=None,
    filename=None,
    margin=60,
):
    """Generate an image from code using Playwright (Chromium) rendering"""

    # Determine lexer for syntax highlighting
    lexer = None
    if language:
        try:
            lexer = get_lexer_by_name(language)
        except:
            print(
                f"Warning: Unknown language '{language}', falling back to auto-detection",
                file=sys.stderr,
            )

    if not lexer and filename:
        try:
            lexer = get_lexer_for_filename(filename)
        except:
            pass

    if not lexer:
        try:
            lexer = guess_lexer(code)
        except:
            lexer = get_lexer_by_name("text")

    # Get Pygments style and extract background color
    try:
        pygments_style_obj = get_style_by_name(style)
    except:
        print(
            f"Warning: Unknown style '{style}', falling back to 'monokai'",
            file=sys.stderr,
        )
        style = "monokai"
        pygments_style_obj = get_style_by_name(style)

    bg_color = pygments_style_obj.background_color

    # Derive window chrome and gradient colors from background
    window_color = lighten_color(bg_color, 0.15)
    gradient_start = lighten_color(bg_color, 0.1)
    gradient_end = darken_color(bg_color, 0.2)

    # Generate highlighted HTML
    formatter = HtmlFormatter(
        style=style,
        linenos="table" if show_line_numbers else False,
        cssclass="highlight",
        noclasses=False,
    )
    highlighted_code = highlight(code, lexer, formatter)
    pygments_css = formatter.get_style_defs(".highlight")

    # Generate window header HTML
    if show_window and show_decorations:
        window_header = """
        <div class="window-header-chrome">
            <div class="window-button red"></div>
            <div class="window-button yellow"></div>
            <div class="window-button green"></div>
        </div>
        """
    elif show_window and not show_decorations:
        window_header = """
        <div class="window-header-chrome"></div>
        """
    elif not show_window and show_decorations:
        window_header = """
        <div class="window-header-clear">
            <div class="window-button red"></div>
            <div class="window-button yellow"></div>
            <div class="window-button green"></div>
        </div>
        """
    else:
        window_header = ""

    # Generate full HTML
    html = HTML_TEMPLATE.format(
        bg_color=bg_color,
        window=window_color,
        gradient_start=gradient_start,
        gradient_end=gradient_end,
        font_size=font_size,
        padding=padding,
        margin=margin,
        window_header=window_header,
        highlighted_code=highlighted_code,
        pygments_css=pygments_css,
    )

    # Use Playwright to render HTML to image
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(
            device_scale_factor=3
        )  # 2x for retina, 3x for extra sharp
        await page.set_content(html)

        # Get the element and take a screenshot
        element = await page.query_selector("body")
        await element.screenshot(path=output)

        await browser.close()

    print(f"Image saved to {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate presentable images of code snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From stdin (pipe) - auto-detect language
  cat script.py | snatch -o output.png
  
  # From file - language detected from extension
  snatch -f script.py -o output.png
  
  # Explicit language and theme
  echo 'print("hello")' | snatch -l python -t monokai -o hello.png
  
  # With custom settings
  cat code.js | snatch -t dracula --font-size 16 -m 80 -o code.png
  
  # No line numbers or window chrome
  snatch -f code.py --no-line-numbers --no-chrome -o code.png
  
  # List all available themes
  snatch --list-themes

Popular themes: monokai, dracula, github-dark, nord, solarized-dark, 
                one-dark, material, gruvbox-dark, zenburn, paraiso-dark

Installation:
  pip install playwright pygments
  playwright install chromium
        """,
    )

    parser.add_argument("-f", "--file", help="Input file (if not using stdin)")
    parser.add_argument(
        "-o", "--output", default="code.png", help="Output file (default: code.png)"
    )
    parser.add_argument(
        "-l",
        "--language",
        help="Language for syntax highlighting (e.g., python, javascript)",
    )
    parser.add_argument(
        "-t",
        "--theme",
        default="monokai",
        help="Pygments theme name (default: monokai). Use any Pygments style.",
    )
    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List all available Pygments themes and exit",
    )
    parser.add_argument(
        "--font-size", type=int, default=12, help="Font size in pixels (default: 12)"
    )
    parser.add_argument(
        "-p",
        "--padding",
        type=int,
        default=20,
        help="Padding inside window in pixels (default: 20)",
    )
    parser.add_argument(
        "-m",
        "--margin",
        type=int,
        default=40,
        help="Margin around window in pixels (default: 40)",
    )
    parser.add_argument(
        "--no-line-numbers", action="store_true", help="Hide line numbers"
    )
    parser.add_argument("--no-chrome", action="store_true", help="Hide window chrome")
    parser.add_argument(
        "--no-decorations", action="store_true", help="Hide window deocrations"
    )

    args = parser.parse_args()

    # Handle --list-styles
    if args.list_themes:
        print("Available Pygments styles:")
        print()
        for style in sorted(get_all_styles()):
            print(f"  {style}")
        print()
        print("Usage: snatch -t <theme> -f <file> -o <output>")
        sys.exit(0)

    # Read code from file or stdin
    if args.file:
        try:
            with open(args.file, "r") as f:
                code = f.read()
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print(
                "Error: No input provided. Use -f for file input or pipe content via stdin.",
                file=sys.stderr,
            )
            print("Try 'snatch --help' for more information.", file=sys.stderr)
            sys.exit(1)
        code = sys.stdin.read()

    if not code.strip():
        print("Error: Input is empty", file=sys.stderr)
        sys.exit(1)

    # Generate image
    try:
        asyncio.run(
            create_code_image(
                code=code,
                style=args.theme,
                font_size=args.font_size,
                padding=args.padding,
                margin=args.margin,
                show_line_numbers=not args.no_line_numbers,
                output=args.output,
                show_window=not args.no_chrome,
                show_decorations=not args.no_decorations,
                language=args.language,
                filename=args.file,
            )
        )
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        print("\nMake sure Playwright and Chromium are installed:", file=sys.stderr)
        print("  pip install playwright pygments", file=sys.stderr)
        print("  playwright install chromium", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
