import os
from PIL import Image, ImageOps
from typing import Tuple, Optional
import io


class ImageOptimizer:
    
    DEFAULT_QUALITY = 85
    DEFAULT_MAX_WIDTH = 1920
    DEFAULT_MAX_HEIGHT = 1080
    THUMBNAIL_SIZE = (300, 300)
    
    @staticmethod
    def optimize_for_web(
        input_path: str,
        output_path: str,
        quality: int = DEFAULT_QUALITY,
        max_width: int = DEFAULT_MAX_WIDTH,
        max_height: int = DEFAULT_MAX_HEIGHT
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Optimize image for web usage
        """
        try:
            # Open and process image
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get original dimensions
                original_width, original_height = img.size
                
                # Calculate new dimensions while maintaining aspect ratio
                ratio = min(max_width / original_width, max_height / original_height)
                
                if ratio < 1:
                    new_width = int(original_width * ratio)
                    new_height = int(original_height * ratio)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    new_width, new_height = original_width, original_height
                
                # Apply auto-orientation
                img = ImageOps.exif_transpose(img)
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save optimized image
                img.save(
                    output_path,
                    format='JPEG',
                    quality=quality,
                    optimize=True,
                    progressive=True
                )
                
                # Calculate compression ratio
                original_size = os.path.getsize(input_path)
                optimized_size = os.path.getsize(output_path)
                compression_ratio = (1 - optimized_size / original_size) * 100
                
                metadata = {
                    'original_dimensions': [original_width, original_height],
                    'optimized_dimensions': [new_width, new_height],
                    'original_size': original_size,
                    'optimized_size': optimized_size,
                    'compression_ratio': round(compression_ratio, 2),
                    'quality': quality
                }
                
                return True, None, metadata
                
        except Exception as e:
            return False, str(e), None
    
    @staticmethod
    def create_thumbnail(
        input_path: str,
        output_path: str,
        size: Tuple[int, int] = THUMBNAIL_SIZE
    ) -> Tuple[bool, Optional[str]]:
        """
        Create thumbnail from image
        """
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Apply auto-orientation
                img = ImageOps.exif_transpose(img)
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save thumbnail
                img.save(output_path, format='JPEG', quality=85, optimize=True)
                
                return True, None
                
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_image_info(file_path: str) -> Optional[dict]:
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'has_transparency': img.mode in ('RGBA', 'LA', 'P')
                }
        except Exception:
            return None
    
    @staticmethod
    def is_optimizable_image(mime_type: str) -> bool:
        optimizable_types = [
            'image/jpeg',
            'image/jpg',
            'image/png',
            'image/bmp',
            'image/tiff',
            'image/webp'
        ]
        return mime_type.lower() in optimizable_types