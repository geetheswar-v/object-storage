import os
import shutil
import subprocess
import json
from PIL import Image, ImageOps
from typing import Tuple


def optimize_image_for_web(
    input_path: str,
    output_path: str,
    quality: int = 80,
    max_width: int = 1200,
    max_height: int = 800,
    preserve_alpha: bool = False
) -> Tuple[bool, str | None]:
    """Optimize image for web usage"""
    try:
        with Image.open(input_path) as img:
            # Get original dimensions
            original_width, original_height = img.size
            has_transparency = img.mode in ('RGBA', 'LA', 'P')
            
            # Handle transparency
            if has_transparency and not preserve_alpha:
                # Convert to RGB with white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            elif has_transparency and preserve_alpha:
                # Keep as RGBA
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            else:
                # Convert to RGB for consistency
                if img.mode != 'RGB':
                    img = img.convert('RGB')
            
            # Resize if needed
            ratio = min(max_width / original_width, max_height / original_height)
            if ratio < 1:
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Apply auto-orientation
            img = ImageOps.exif_transpose(img)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save optimized image
            if has_transparency and preserve_alpha:
                img.save(output_path, format='PNG', optimize=True, compress_level=6)
            else:
                img.save(output_path, format='JPEG', quality=quality, optimize=True, progressive=True)
            
            return True, None
            
    except Exception as e:
        return False, str(e)


def check_ffmpeg_available() -> bool:
    """Check if ffmpeg is available on the system (cross-platform)"""
    try:
        # Try to run ffmpeg -version
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def get_video_info(input_path: str) -> dict | None:
    """Get video information using ffprobe (cross-platform)"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', input_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                return {
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'duration': float(data.get('format', {}).get('duration', 0)),
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'bitrate': int(data.get('format', {}).get('bit_rate', 0))
                }
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def optimize_video_for_web(
    input_path: str,
    output_path: str,
    max_width: int = 1280,
    max_height: int = 720,
    quality: str = "medium"
) -> Tuple[bool, str | None]:
    """Optimize video for web usage using ffmpeg (cross-platform)"""
    
    # Check if ffmpeg is available
    if not check_ffmpeg_available():
        # Fallback to copying the file
        try:
            shutil.copy2(input_path, output_path)
            return True, "FFmpeg not available - file copied without optimization"
        except Exception as e:
            return False, str(e)
    
    try:
        # Get video info to check if we need to resize
        video_info = get_video_info(input_path)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Only create if dirname is not empty
            os.makedirs(output_dir, exist_ok=True)
        
        # Build ffmpeg command
        cmd = ['ffmpeg', '-i', input_path, '-y']  # -y to overwrite output file
        
        # Video codec settings
        cmd.extend(['-c:v', 'libx264'])
        
        # Quality settings
        if quality == "high":
            cmd.extend(['-crf', '18'])
        elif quality == "medium":
            cmd.extend(['-crf', '23'])
        elif quality == "low":
            cmd.extend(['-crf', '28'])
        else:
            cmd.extend(['-crf', '23'])  # default to medium
        
        # Resize if needed
        if video_info and video_info['width'] > 0 and video_info['height'] > 0:
            current_width = video_info['width']
            current_height = video_info['height']
            
            # Calculate scaling while maintaining aspect ratio
            scale_factor = min(max_width / current_width, max_height / current_height)
            
            if scale_factor < 1:
                new_width = int(current_width * scale_factor)
                new_height = int(current_height * scale_factor)
                
                # Ensure even dimensions (required for some codecs)
                new_width = new_width if new_width % 2 == 0 else new_width - 1
                new_height = new_height if new_height % 2 == 0 else new_height - 1
                
                cmd.extend(['-vf', f'scale={new_width}:{new_height}'])
        
        # Audio codec settings
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
        
        # Output settings for web
        cmd.extend([
            '-preset', 'medium',  # Balance between speed and compression
            '-movflags', '+faststart',  # Enable fast start for web streaming
            '-f', 'mp4'  # Force MP4 format
        ])
        
        # Add output path
        cmd.append(output_path)
        
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            return True, None
        else:
            return False, f"FFmpeg error: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "Video optimization timed out"
    except Exception as e:
        return False, str(e)


def is_optimizable_image(mime_type: str) -> bool:
    """Check if image can be optimized (exclude SVG)"""
    return mime_type.lower() in [
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/bmp',
        'image/tiff',
        'image/webp'
    ]


def is_optimizable_video(mime_type: str) -> bool:
    """Check if video can be optimized"""
    return mime_type.lower().startswith('video/')