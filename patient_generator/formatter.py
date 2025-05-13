import os
import json
import gzip
import datetime
from xml.dom.minidom import parseString
import dicttoxml

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

class OutputFormatter:
    """Formats FHIR bundles for output"""
    
    def __init__(self):
        self.nfc_mime_types = {
            "plain": "application/x.ips.v1-0",
            "gzip": "application/x.ips.gzip.v1-0",
            "encrypted": "application/x.ips.aes256.v1-0",
            "gzip_encrypted": "application/x.ips.gzip.aes256.v1-0"
        }
    
    def format_json(self, bundles):
        """Format bundles as JSON"""
        return json.dumps(bundles, indent=2)
    
    def format_xml(self, bundles):
        """Format bundles as XML"""
        # Use dicttoxml to convert dict to XML
        xml_data = dicttoxml.dicttoxml(bundles, custom_root='PatientBundles', attr_type=False)
        
        # Format XML for better readability
        try:
            dom = parseString(xml_data)
            pretty_xml = dom.toprettyxml()
            return pretty_xml
        except Exception as e:
            print(f"Warning: XML pretty formatting failed: {e}")
            return xml_data.decode('utf-8')
    
    def compress_gzip(self, data):
        """Compress data using gzip"""
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        return gzip.compress(data)
    
    def encrypt_aes(self, data, key):
        """Encrypt data using AES-256-GCM"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography package is required for encryption")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        # Generate a random 16-byte initialization vector
        iv = os.urandom(16)
        
        # Create an encryptor object
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt the data
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Get the tag (MAC)
        tag = encryptor.tag
        
        # Return IV + MAC + ciphertext
        return iv + tag + ciphertext
    
    def format_ndef(self, data, format_type="plain"):
        """Format data as NDEF message with appropriate mime type"""
        mime_type = self.nfc_mime_types.get(format_type, self.nfc_mime_types["plain"])
        
        # NDEF header construction (simplified)
        # In a real implementation, this would create the actual binary NDEF message
        ndef_message = {
            "header": {
                "TNF": 0x02,  # Media type
                "IL": 0,      # No ID Length field
                "MB": 1,      # Message Begin
                "ME": 1,      # Message End
                "CF": 0,      # Not chunked
                "SR": 0,      # Not a short record
                "type": mime_type
            },
            "payload": data
        }
        
        return ndef_message
    
    def create_output_files(self, bundles, output_dir, formats=None, use_compression=True, use_encryption=False, encryption_key=None):
        """Create all required output files"""
        if formats is None:
            formats = ["json", "xml"]
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = []
        
        # JSON format
        if "json" in formats:
            json_data = self.format_json(bundles)
            json_path = os.path.join(output_dir, "patients.json")
            with open(json_path, "w") as f:
                f.write(json_data)
            output_files.append(json_path)
            
            # Compressed JSON
            if use_compression:
                gzip_json_data = self.compress_gzip(json_data)
                gzip_json_path = os.path.join(output_dir, "patients.json.gz")
                with open(gzip_json_path, "wb") as f:
                    f.write(gzip_json_data)
                output_files.append(gzip_json_path)
            
            # Encrypted JSON
            if use_encryption and encryption_key:
                encrypted_json_data = self.encrypt_aes(json_data, encryption_key)
                encrypted_json_path = os.path.join(output_dir, "patients.json.enc")
                with open(encrypted_json_path, "wb") as f:
                    f.write(encrypted_json_data)
                output_files.append(encrypted_json_path)
                
                # Compressed and encrypted JSON
                if use_compression:
                    gzip_json_data = self.compress_gzip(json_data)
                    gzip_encrypted_json_data = self.encrypt_aes(gzip_json_data, encryption_key)
                    gzip_encrypted_json_path = os.path.join(output_dir, "patients.json.gz.enc")
                    with open(gzip_encrypted_json_path, "wb") as f:
                        f.write(gzip_encrypted_json_data)
                    output_files.append(gzip_encrypted_json_path)
        
        # XML format
        if "xml" in formats:
            xml_data = self.format_xml(bundles)
            xml_path = os.path.join(output_dir, "patients.xml")
            with open(xml_path, "w") as f:
                f.write(xml_data)
            output_files.append(xml_path)
            
            # Compressed XML
            if use_compression:
                gzip_xml_data = self.compress_gzip(xml_data)
                gzip_xml_path = os.path.join(output_dir, "patients.xml.gz")
                with open(gzip_xml_path, "wb") as f:
                    f.write(gzip_xml_data)
                output_files.append(gzip_xml_path)
            
            # Encrypted XML
            if use_encryption and encryption_key:
                encrypted_xml_data = self.encrypt_aes(xml_data, encryption_key)
                encrypted_xml_path = os.path.join(output_dir, "patients.xml.enc")
                with open(encrypted_xml_path, "wb") as f:
                    f.write(encrypted_xml_data)
                output_files.append(encrypted_xml_path)
                
                # Compressed and encrypted XML
                if use_compression:
                    gzip_xml_data = self.compress_gzip(xml_data)
                    gzip_encrypted_xml_data = self.encrypt_aes(gzip_xml_data, encryption_key)
                    gzip_encrypted_xml_path = os.path.join(output_dir, "patients.xml.gz.enc")
                    with open(gzip_encrypted_xml_path, "wb") as f:
                        f.write(gzip_encrypted_xml_data)
                    output_files.append(gzip_encrypted_xml_path)
        
        # Create sample NDEF files
        if bundles:
            sample_bundle = bundles[0]
            sample_json = json.dumps(sample_bundle)
            
            # Plain NDEF
            plain_ndef = self.format_ndef(sample_json, "plain")
            plain_ndef_path = os.path.join(output_dir, "sample_plain.ndef.json")
            with open(plain_ndef_path, "w") as f:
                f.write(json.dumps(plain_ndef, indent=2))
            output_files.append(plain_ndef_path)
            
            # Gzipped NDEF
            if use_compression:
                gzipped_data = self.compress_gzip(sample_json)
                gzip_ndef = self.format_ndef(gzipped_data, "gzip")
                gzip_ndef_path = os.path.join(output_dir, "sample_gzip.ndef.bin")
                with open(gzip_ndef_path, "wb") as f:
                    f.write(gzipped_data)
                output_files.append(gzip_ndef_path)
            
            # Encrypted NDEF
            if use_encryption and encryption_key:
                encrypted_data = self.encrypt_aes(sample_json.encode('utf-8'), encryption_key)
                encrypted_ndef = self.format_ndef(encrypted_data, "encrypted")
                encrypted_ndef_path = os.path.join(output_dir, "sample_encrypted.ndef.bin")
                with open(encrypted_ndef_path, "wb") as f:
                    f.write(encrypted_data)
                output_files.append(encrypted_ndef_path)
                
                # Gzipped and encrypted NDEF
                if use_compression:
                    gzipped_json = self.compress_gzip(sample_json)
                    gzip_encrypted_data = self.encrypt_aes(gzipped_json, encryption_key)
                    gzip_encrypted_ndef = self.format_ndef(gzip_encrypted_data, "gzip_encrypted")
                    gzip_encrypted_ndef_path = os.path.join(output_dir, "sample_gzip_encrypted.ndef.bin")
                    with open(gzip_encrypted_ndef_path, "wb") as f:
                        f.write(gzip_encrypted_data)
                    output_files.append(gzip_encrypted_ndef_path)
        
        return output_files