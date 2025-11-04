"""
QR Code Generation Service
Powered by Erkan ERDEM
"""
import qrcode
import io
import base64
from typing import Tuple, Optional


class QRCodeService:
    """Service for QR code generation and management"""

    @staticmethod
    def generate_qr_code(data: str,
                        box_size: int = 10,
                        border: int = 5,
                        error_correction: int = qrcode.constants.ERROR_CORRECT_H) -> Tuple[bytes, str]:
        """
        Generate QR code image from data

        Args:
            data: Data to encode in QR code (can be URL or data string)
            box_size: Size of each box in pixels
            border: Border size in boxes
            error_correction: Error correction level

        Returns:
            Tuple of (PNG bytes, base64 data URI)
        """
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            box_size=box_size,
            border=border,
            error_correction=error_correction
        )

        # Add data and make QR code
        qr.add_data(data)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to PNG bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        png_bytes = buffer.getvalue()

        # Create base64 data URI
        img_base64 = base64.b64encode(png_bytes).decode('utf-8')
        data_uri = f"data:image/png;base64,{img_base64}"

        return png_bytes, data_uri
    
    @staticmethod
    def generate_location_url(location_id: int, hotel_id: int, base_url: str = None) -> str:
        """
        Generate guest call URL for a location
        
        Args:
            location_id: Location ID
            hotel_id: Hotel ID
            base_url: Base URL (e.g., https://buggycall.com)
        
        Returns:
            Full URL for guest to call buggy
        """
        if not base_url:
            # Try to get from environment or use default
            import os
            base_url = os.getenv('APP_BASE_URL', 'http://localhost:5000')
        
        return f"{base_url}/guest/call?location={location_id}&hotel={hotel_id}"

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
