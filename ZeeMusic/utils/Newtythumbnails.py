import os
import re
import random
import aiofiles
import aiohttp
import logging
import traceback
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch

logging.basicConfig(level=logging.INFO)

# Modern design constants
GLASS_ALPHA = 120
BLUR_RADIUS = 20
MODERN_COLORS = [
    (255, 50, 100),    # Vibrant Pink
    (50, 200, 255),    # Electric Blue
    (100, 255, 150),   # Neon Green
    (255, 150, 50),    # Orange
    (180, 80, 255),    # Purple
    (255, 100, 200),   # Hot Pink
]

def get_vibrant_color():
    return random.choice(MODERN_COLORS)

def create_glass_panel(width, height, color):
    """Create modern glass morphism effect"""
    glass = Image.new('RGBA', (width, height), (*color, GLASS_ALPHA))
    
    # Add subtle noise for texture
    draw = ImageDraw.Draw(glass)
    for _ in range(width * height // 100):  # Add some noise points
        x, y = random.randint(0, width-1), random.randint(0, height-1)
        r, g, b, a = glass.getpixel((x, y))
        brightness = random.randint(-20, 20)
        new_color = (
            max(0, min(255, r + brightness)),
            max(0, min(255, g + brightness)),
            max(0, min(255, b + brightness)),
            a
        )
        draw.point((x, y), fill=new_color)
    
    return glass

def add_modern_text(draw, position, text, font, fill_color, shadow=True):
    """Add text with modern shadow effects"""
    x, y = position
    
    if shadow:
        # Multiple shadow layers for depth
        shadow_colors = [(0, 0, 0, 100), (0, 0, 0, 50), (0, 0, 0, 25)]
        for i, shadow_color in enumerate(shadow_colors):
            offset = 2 + i
            draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    
    # Main text
    draw.text((x, y), text, font=font, fill=fill_color)

def create_modern_thumbnail(image, size, border_color):
    """Create modern thumbnail with glass border"""
    # Resize image
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    
    # Create circular mask
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    
    # Apply glass border effect
    border_size = 15
    bordered_size = size + border_size * 2
    
    # Create glass border
    border = Image.new('RGBA', (bordered_size, bordered_size), (*border_color, 150))
    border_mask = Image.new('L', (bordered_size, bordered_size), 0)
    border_draw = ImageDraw.Draw(border_mask)
    border_draw.ellipse((0, 0, bordered_size, bordered_size), fill=255)
    
    # Composite everything
    final_image = Image.new('RGBA', (bordered_size, bordered_size), (0, 0, 0, 0))
    final_image.paste(border, (0, 0), border_mask)
    final_image.paste(image, (border_size, border_size), mask)
    
    return final_image

def create_modern_progress_bar(draw, position, width, height, progress, is_live=False):
    """Create modern gradient progress bar"""
    x, y = position
    
    if is_live:
        # Red bar for live stream
        draw.rounded_rectangle([x, y, x + width, y + height], radius=height//2, fill=(255, 0, 0, 200))
        # Live indicator dot
        draw.ellipse([x + width - 10, y - 5, x + width + 5, y + height + 5], fill=(255, 0, 0))
    else:
        # Gradient progress bar
        progress_width = int(width * progress)
        
        # Background
        draw.rounded_rectangle([x, y, x + width, y + height], radius=height//2, fill=(100, 100, 100, 150))
        
        # Progress with gradient
        for i in range(progress_width):
            # Simple gradient effect
            ratio = i / width
            color = (
                int(50 + ratio * 200),
                int(100 + ratio * 155),
                int(150 + ratio * 105),
                255
            )
            draw.rectangle([x + i, y, x + i + 1, y + height], fill=color)
        
        # Progress circle
        circle_x = x + progress_width
        draw.ellipse([circle_x - 8, y - 4, circle_x + 8, y + height + 4], fill=(255, 255, 255))

async def gen_thumb(videoid: str):
    try:
        if os.path.isfile(f"cache/{videoid}_pro.png"):
            return f"cache/{videoid}_pro.png"

        # Fetch YouTube data
        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        
        for result in (await results.next())["result"]:
            title = result.get("title", "Unsupported Title")
            title = re.sub("\W+", " ", title).title()[:50] + "..." if len(title) > 50 else title
            
            duration = result.get("duration", "Live")
            is_live = duration == "Live" or not duration
            
            thumbnail_data = result.get("thumbnails")
            thumbnail = thumbnail_data[0]["url"].split("?")[0] if thumbnail_data else None
            
            views_data = result.get("viewCount", {})
            views = views_data.get("short", "Unknown Views") if views_data else "Unknown Views"
            
            channel_data = result.get("channel", {})
            channel = channel_data.get("name", "Unknown Channel") if channel_data else "Unknown Channel"

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    filepath = f"cache/thumb{videoid}.jpg"
                    async with aiofiles.open(filepath, "wb") as f:
                        await f.write(await resp.read())

        # Image processing
        youtube = Image.open(f"cache/thumb{videoid}.jpg")
        base_image = youtube.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # Enhanced background with glass effect
        background = base_image.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        # Add vibrant gradient overlay
        vibrant_color = get_vibrant_color()
        gradient = create_glass_panel(1280, 720, vibrant_color)
        background = Image.alpha_composite(background.convert('RGBA'), gradient)
        
        draw = ImageDraw.Draw(background)
        
        # Modern fonts
        title_font = ImageFont.truetype("ZeeMusic/assets/font3.ttf", 48)
        meta_font = ImageFont.truetype("ZeeMusic/assets/font2.ttf", 28)
        small_font = ImageFont.truetype("ZeeMusic/assets/font.ttf", 24)
        
        # Create modern thumbnail
        thumbnail_size = 350
        modern_thumb = create_modern_thumbnail(youtube, thumbnail_size - 50, vibrant_color)
        thumb_x, thumb_y = 80, 180
        background.paste(modern_thumb, (thumb_x, thumb_y), modern_thumb)
        
        # Text positions
        text_x = thumb_x + thumbnail_size + 40
        text_y = thumb_y + 30
        
        # Glass text panel
        panel_width = 1280 - text_x - 40
        glass_panel = create_glass_panel(panel_width, 200, (30, 30, 40))
        background.alpha_composite(glass_panel, (text_x - 20, text_y - 20))
        
        # Title with modern shadow
        title_lines = []
        current_line = ""
        for word in title.split():
            test_line = current_line + " " + word if current_line else word
            if meta_font.getlength(test_line) <= panel_width - 40:
                current_line = test_line
            else:
                if current_line:
                    title_lines.append(current_line)
                current_line = word
        if current_line:
            title_lines.append(current_line)
        
        # Render title lines
        for i, line in enumerate(title_lines[:2]):  # Max 2 lines
            add_modern_text(draw, (text_x, text_y + i * 50), line, title_font, (255, 255, 255))
        
        # Metadata
        meta_y = text_y + 120
        add_modern_text(draw, (text_x, meta_y), f"🎵 {channel}", meta_font, (200, 200, 255))
        add_modern_text(draw, (text_x, meta_y + 35), f"👁️ {views}", meta_font, (200, 255, 200))
        
        # Progress bar
        bar_y = meta_y + 90
        progress = random.uniform(0.3, 0.7) if not is_live else 1.0
        create_modern_progress_bar(draw, (text_x, bar_y), 500, 10, progress, is_live)
        
        # Time indicators
        time_y = bar_y + 25
        add_modern_text(draw, (text_x, time_y), "00:00", small_font, (200, 200, 200))
        
        duration_text = "🔴 LIVE" if is_live else f"{duration}"
        duration_width = small_font.getlength(duration_text)
        add_modern_text(draw, (text_x + 500 - duration_width, time_y), duration_text, small_font, 
                       (255, 0, 0) if is_live else (255, 255, 255))
        
        # Modern play controls
        controls_size = 300
        controls = Image.open("ZeeMusic/assets/play_icons.png")
        controls = controls.resize((controls_size, 60), Image.Resampling.LANCZOS)
        controls_x = text_x + (500 - controls_size) // 2
        background.paste(controls, (controls_x, bar_y + 60), controls)
        
        # Cleanup
        os.remove(f"cache/thumb{videoid}.jpg")
        
        # Save final image
        background_path = f"cache/{videoid}_pro.png"
        background.save(background_path, quality=95)
        
        return background_path

    except Exception as e:
        logging.error(f"Error generating thumbnail for video {videoid}: {e}")
        traceback.print_exc()
        return None
