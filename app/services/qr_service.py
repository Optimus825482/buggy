"""
QR Code Generation Service
Powered by Erkan ERDEM
"""
import qrcode
import qrcode.image.svg
import io
import base64
from typing import Tuple, Optional


class QRCodeService:
    """Service for QR code generation and management"""

    @staticmethod
    def generate_qr_code(data: str,
                        box_size: int = 2,
                        border: int = 0,
                        error_correction: int = qrcode.constants.ERROR_CORRECT_L,
                        format: str = 'svg') -> Tuple[bytes, str]:
        """
        Generate QR code image from data (SVG veya PNG)

        Args:
            data: QR kodda encode edilecek veri (URL veya data string)
            box_size: Her kutunun pixel boyutu (varsayılan: 2 - çok düşük yoğunluk)
            border: Kenar boşluğu kutu sayısı (varsayılan: 0 - kenarsız)
            error_correction: Hata düzeltme seviyesi (varsayılan: L - %7, en düşük)
            format: Çıktı formatı ('svg' 800x800 veya 'png')

        Returns:
            Tuple of (bytes, base64 data URI)
        """
        try:
            # QR code instance oluştur
            qr = qrcode.QRCode(
                version=1,  # Otomatik boyutlandırma
                box_size=box_size,
                border=border,
                error_correction=error_correction
            )

            # Veriyi ekle ve oluştur
            qr.add_data(data)
            qr.make(fit=True)

            if format.lower() == 'svg':
                # SVG formatında oluştur (daha temiz, ölçeklenebilir)
                factory = qrcode.image.svg.SvgPathImage
                img = qr.make_image(image_factory=factory, fill_color="black", back_color="white")
                
                # SVG bytes'a çevir
                buffer = io.BytesIO()
                img.save(buffer)
                svg_bytes = buffer.getvalue()
                
                # SVG içeriğini oku ve width/height ekle
                svg_str = svg_bytes.decode('utf-8')
                
                # SVG tag'ini bul ve width/height ekle (800x800 büyük boyut)
                if '<svg' in svg_str and 'width=' not in svg_str:
                    svg_str = svg_str.replace('<svg', '<svg width="800" height="800"', 1)
                elif '<svg' in svg_str:
                    # Mevcut width/height varsa değiştir
                    import re
                    svg_str = re.sub(r'width="[^"]*"', 'width="800"', svg_str)
                    svg_str = re.sub(r'height="[^"]*"', 'height="800"', svg_str)
                
                svg_bytes = svg_str.encode('utf-8')
                
                # Base64 data URI oluştur
                img_base64 = base64.b64encode(svg_bytes).decode('utf-8')
                data_uri = f"data:image/svg+xml;base64,{img_base64}"
                
                return svg_bytes, data_uri
            else:
                # PNG formatında oluştur
                img = qr.make_image(fill_color="black", back_color="white")
                
                # PNG bytes'a çevir
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                png_bytes = buffer.getvalue()
                
                # Base64 data URI oluştur
                img_base64 = base64.b64encode(png_bytes).decode('utf-8')
                data_uri = f"data:image/png;base64,{img_base64}"
                
                return png_bytes, data_uri
                
        except Exception as e:
            # Hata durumunda loglama ve yeniden fırlat
            import logging
            logging.error(f"QR kod oluşturma hatası: {str(e)}")
            raise
    
    @staticmethod
    def generate_location_url(location_id: int, hotel_id: int, base_url: str = None) -> str:
        """
        Generate guest call URL for a location (kısa parametre formatı)
        
        Args:
            location_id: Location ID
            hotel_id: Hotel ID
            base_url: Base URL (e.g., https://buggycall.com)
        
        Returns:
            Full URL for guest to call buggy (kısa format: ?l=id&h=hotel)
        """
        if not base_url:
            # Try to get from environment or use default
            import os
            base_url = os.getenv('APP_BASE_URL', 'http://localhost:5000')
        
        # Kısa parametre isimleri kullan: l=location, h=hotel
        return f"{base_url}/guest/call?l={location_id}&h={hotel_id}"

    @staticmethod
    def generate_location_qr_data(hotel_id: int, sequence: int) -> str:
        """
        Generate unique QR code data for a location

        Args:
            hotel_id: Hotel ID
            sequence: Location sequence number

        Returns:
            Formatted QR code data string
        """
        return f"LOC{hotel_id}{sequence:04d}"

    @staticmethod
    def parse_location_qr_data(qr_data: str) -> Optional[Tuple[int, int]]:
        """
        Parse location QR code data

        Args:
            qr_data: QR code data string (e.g., "LOC10001")

        Returns:
            Tuple of (hotel_id, sequence) or None if invalid
        """
        try:
            if not qr_data.startswith("LOC"):
                return None

            # Extract numeric part
            numeric_part = qr_data[3:]

            # First digit(s) is hotel_id, last 4 digits is sequence
            if len(numeric_part) < 5:
                return None

            hotel_id = int(numeric_part[:-4])
            sequence = int(numeric_part[-4:])

            return hotel_id, sequence
        except (ValueError, IndexError):
            return None

    @staticmethod
    def validate_qr_data(qr_data: str) -> bool:
        """
        Validate QR code data format

        Args:
            qr_data: QR code data to validate

        Returns:
            True if valid, False otherwise
        """
        return QRCodeService.parse_location_qr_data(qr_data) is not None

    @staticmethod
    def delete_qr_code(location_id: int) -> None:
        """
        Delete QR code file for a location
        
        Args:
            location_id: Location ID whose QR code should be deleted
        
        Note:
            This is a placeholder for QR code file deletion.
            Currently QR codes are generated on-demand and not stored as files.
            If file storage is implemented in the future, this method should
            handle the actual file deletion.
        """
        # QR codes are currently generated on-demand and stored in database
        # No physical file deletion needed
        pass
