import atexit
import gzip
import json
import logging
import os
import shutil
import tempfile
from xml.dom.minidom import parseString

import dicttoxml

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class OutputFormatter:
    """Formats FHIR bundles for output with memory optimization for large datasets"""

    # Constants for KDF and Encryption
    KDF_SALT_SIZE = 16  # bytes
    KDF_ITERATIONS = 600000  # OWASP recommendation for PBKDF2-HMAC-SHA256
    AES_KEY_SIZE = 32  # bytes for AES-256
    GCM_IV_SIZE = 16  # bytes for GCM IV
    # GCM tag is typically 16 bytes (128 bits)

    def __init__(self):
        self.nfc_mime_types = {
            "plain": "application/x.ips.v1-0",
            "gzip": "application/x.ips.gzip.v1-0",
            "encrypted": "application/x.ips.aes256.v1-0",
            "gzip_encrypted": "application/x.ips.gzip.aes256.v1-0",
        }

        # Create a temp directory that will be cleaned up when the program exits
        self.temp_dir = tempfile.mkdtemp(prefix="patient_gen_")

        # Register cleanup function to ensure temp files are removed
        atexit.register(self._cleanup_temp_files)

        # Track all temporary files created
        self.temp_files = []

        # Set up logging
        self.logger = logging.getLogger("OutputFormatter")

    def _cleanup_temp_files(self):
        """Clean up all temporary files and the temp directory"""
        # Remove individual temp files first
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")

        # Then remove the temp directory
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Failed to remove temp directory {self.temp_dir}: {e}")

    def _create_temp_file(self, suffix=None):
        """Create a new temporary file and track it for cleanup"""
        fd, temp_path = tempfile.mkstemp(dir=self.temp_dir, suffix=suffix)
        os.close(fd)  # Close the file descriptor
        self.temp_files.append(temp_path)
        return temp_path

    def format_json(self, bundles, stream=None):
        """Format bundles as JSON with metadata, optionally writing to a stream for memory efficiency"""
        from datetime import datetime

        # Create metadata wrapper
        metadata = {
            "metadata": {
                "patient_count": len(bundles),
                "generated_at": datetime.now().strftime("%Y%m%d"),  # ISO standard YYYYMMDD format
                "generated_at_iso": datetime.now().isoformat(),  # Full ISO timestamp for precision
                "generator_version": "2.0.0",
            },
            "patients": bundles,
        }

        if stream:
            # Memory-efficient streaming for large datasets (compact JSON)
            stream.write('{"metadata":')
            json.dump(metadata["metadata"], stream, separators=(",", ":"))
            stream.write(',"patients":[')
            for i, bundle in enumerate(bundles):
                if i > 0:
                    stream.write(",")
                # Compact JSON without indentation
                json.dump(bundle, stream, separators=(",", ":"))
            stream.write("]}")
            return None
        # Standard in-memory approach for smaller datasets (compact)
        return json.dumps(metadata, separators=(",", ":"))

    def format_xml(self, bundles, stream=None):
        """Format bundles as XML, optionally using a stream for memory efficiency"""
        if stream:
            # For large datasets, process bundles one by one
            root_element = '<?xml version="1.0" encoding="utf-8"?>\n<PatientBundles>\n'
            # Write as bytes if stream is binary mode
            if hasattr(stream, "mode") and "b" in stream.mode:
                stream.write(root_element.encode("utf-8"))
            else:
                stream.write(root_element)

            for bundle in bundles:
                # Convert each bundle to XML
                bundle_xml_output = dicttoxml.dicttoxml(bundle, attr_type=False, root=False)
                # dicttoxml can return either bytes or str
                if isinstance(bundle_xml_output, bytes):
                    bundle_xml_str = bundle_xml_output.decode("utf-8")
                else:
                    bundle_xml_str = bundle_xml_output

                # Write directly to stream
                # Check if stream is binary mode
                if hasattr(stream, "mode") and "b" in stream.mode:
                    stream.write(bundle_xml_str.encode("utf-8"))
                    stream.write(b"\n")
                else:
                    stream.write(bundle_xml_str)
                    stream.write("\n")

            # Close the root element
            if hasattr(stream, "mode") and "b" in stream.mode:
                stream.write(b"</PatientBundles>")
            else:
                stream.write("</PatientBundles>")
            return None
        # Standard approach for small datasets
        xml_data_output = dicttoxml.dicttoxml(bundles, custom_root="PatientBundles", attr_type=False)
        # dicttoxml always returns bytes
        xml_data_to_parse = xml_data_output

        # Format XML for better readability
        try:
            # parseString can take bytes or str.
            dom = parseString(xml_data_to_parse)
            pretty_xml: str = dom.toprettyxml()
            return pretty_xml
        except Exception as e:
            print(f"Warning: XML pretty formatting failed: {e}")
            # If parsing failed, return the original data, decoded if it was bytes
            if isinstance(xml_data_to_parse, bytes):
                return xml_data_to_parse.decode("utf-8")
            return xml_data_to_parse  # It's already a string

    def compress_gzip(self, data):
        """Compress data using gzip"""
        if isinstance(data, str):
            data = data.encode("utf-8")

        return gzip.compress(data)

    def compress_stream(self, input_stream, output_stream):
        """Compress data from one stream to another using gzip"""
        with gzip.GzipFile(fileobj=output_stream, mode="wb") as gzip_out:
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = input_stream.read(chunk_size)
                if not chunk:
                    break
                gzip_out.write(chunk)

    def encrypt_aes(self, data, password):
        """
        Encrypt data using AES-256-GCM with a key derived from password.
        The password is used to derive an AES key using PBKDF2.
        A random salt is generated for PBKDF2 and prepended to the output.
        A random IV is generated for GCM and prepended to the output.
        Output format: kdf_salt (16B) + gcm_iv (16B) + gcm_tag (16B) + ciphertext
        """
        assert CRYPTO_AVAILABLE, "Cryptography package is required for encryption but not found."
        if (
            not CRYPTO_AVAILABLE
        ):  # This check is redundant due to assert but good for logical flow if assert is disabled
            msg = "Cryptography package is required for encryption"
            raise ImportError(msg)

        if isinstance(data, str):
            data = data.encode("utf-8")

        if not isinstance(password, str):
            msg = "Password must be a string."
            raise TypeError(msg)

        # 1. Generate KDF salt
        kdf_salt = os.urandom(self.KDF_SALT_SIZE)

        # 2. Derive AES key using PBKDF2HMAC
        pbkdf2 = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.AES_KEY_SIZE,
            salt=kdf_salt,
            iterations=self.KDF_ITERATIONS,
            backend=default_backend(),
        )
        aes_key = pbkdf2.derive(password.encode("utf-8"))

        # 3. Generate a random GCM initialization vector (IV)
        gcm_iv = os.urandom(self.GCM_IV_SIZE)

        # 4. Create an encryptor object
        cipher = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(gcm_iv),  # GCM tag is typically 16 bytes
            backend=default_backend(),
        )
        encryptor = cipher.encryptor()

        # 5. Encrypt the data
        ciphertext = encryptor.update(data) + encryptor.finalize()

        # 6. Get the GCM tag (MAC)
        gcm_tag = encryptor.tag  # This is typically 16 bytes for AES-GCM

        # 7. Return kdf_salt + gcm_iv + gcm_tag + ciphertext
        return kdf_salt + gcm_iv + gcm_tag + ciphertext

    def encrypt_stream(self, input_stream, output_stream, password):
        """Encrypt data from one stream to another using AES-256-GCM with key derivation."""
        assert CRYPTO_AVAILABLE, "Cryptography package is required for encryption but not found."
        if not CRYPTO_AVAILABLE:  # Redundant with assert, but explicit
            msg = "Cryptography package is required for encryption"
            raise ImportError(msg)

        # Read input data into memory - GCM mode requires entire data
        # This is a limitation of the GCM mode which doesn't support streaming
        data = input_stream.read()

        # Encrypt using regular method (which now handles key derivation)
        encrypted_data = self.encrypt_aes(data, password)

        # Write to output stream
        output_stream.write(encrypted_data)

    def format_ndef(self, data, format_type="plain"):
        """Format data as NDEF message with appropriate mime type"""
        mime_type = self.nfc_mime_types.get(format_type, self.nfc_mime_types["plain"])

        # NDEF header construction (simplified)
        # In a real implementation, this would create the actual binary NDEF message
        return {
            "header": {
                "TNF": 0x02,  # Media type
                "IL": 0,  # No ID Length field
                "MB": 1,  # Message Begin
                "ME": 1,  # Message End
                "CF": 0,  # Not chunked
                "SR": 0,  # Not a short record
                "type": mime_type,
            },
            "payload": data,
        }

    def create_output_files(
        self,
        bundles,
        output_dir,
        formats=None,
        use_compression=True,
        use_encryption=False,
        encryption_password=None,
        is_chunk=False,
        chunk_index=0,
    ):
        """Create all required output files with streaming options for large datasets"""
        if formats is None:
            formats = ["json", "xml"]

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        output_files = []

        # JSON format
        if "json" in formats:
            if is_chunk:
                # For chunks, append to existing file or create new chunk file
                json_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.json")
                with open(json_path, "w") as f:
                    self.format_json(bundles, stream=f)
            else:
                # Standard output for complete dataset with timestamped filename
                from datetime import datetime

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                patient_count = len(bundles)
                # Keep both old and new filenames for compatibility
                json_path = os.path.join(output_dir, "patients.json")
                json_path_timestamped = os.path.join(output_dir, f"patients_{patient_count}_{timestamp}.json")

                # Check if the dataset is large enough to warrant streaming
                if len(bundles) > 1000:
                    # Write to timestamped file
                    with open(json_path_timestamped, "w") as f:
                        self.format_json(bundles, stream=f)
                    # Also write to standard file for backward compatibility
                    with open(json_path, "w") as f:
                        self.format_json(bundles, stream=f)
                else:
                    # Small dataset, use in-memory processing
                    json_data = self.format_json(bundles)
                    if isinstance(json_data, str):
                        # Write to timestamped file
                        with open(json_path_timestamped, "w") as f:
                            f.write(json_data)
                        # Also write to standard file for backward compatibility
                        with open(json_path, "w") as f:
                            f.write(json_data)
                    else:
                        # This case should ideally not be reached if len(bundles) <= 1000
                        self.logger.warning("json_data was not a string for small dataset JSON processing.")

            output_files.append(json_path_timestamped)  # Add timestamped file to output list
            output_files.append(json_path)

            # Compressed JSON
            if use_compression:
                if is_chunk:
                    gzip_json_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.json.gz")
                else:
                    gzip_json_path = os.path.join(output_dir, "patients.json.gz")

                # Use streaming compression for large datasets
                if len(bundles) > 1000 or is_chunk:  # Apply streaming for chunks too
                    with open(json_path, "rb") as f_in, open(gzip_json_path, "wb") as f_out:
                        self.compress_stream(f_in, f_out)
                else:
                    # Small dataset, use in-memory compression
                    with open(json_path, "rb") as f:
                        json_data = f.read()
                    gzip_json_data = self.compress_gzip(json_data)
                    with open(gzip_json_path, "wb") as f:
                        f.write(gzip_json_data)

                output_files.append(gzip_json_path)

            # Encrypted JSON
            if use_encryption and encryption_password:
                if is_chunk:
                    encrypted_json_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.json.enc")
                else:
                    encrypted_json_path = os.path.join(output_dir, "patients.json.enc")

                # Use streaming encryption for large datasets
                with open(json_path, "rb") as f_in, open(encrypted_json_path, "wb") as f_out:
                    self.encrypt_stream(f_in, f_out, encryption_password)

                output_files.append(encrypted_json_path)

                # Compressed and encrypted JSON
                if use_compression:
                    if is_chunk:
                        gzip_encrypted_json_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.json.gz.enc")
                    else:
                        gzip_encrypted_json_path = os.path.join(output_dir, "patients.json.gz.enc")

                    # Create temporary compressed file
                    temp_gz_path = self._create_temp_file(suffix=".json.gz")

                    try:
                        # First compress
                        with open(json_path, "rb") as f_in, open(temp_gz_path, "wb") as f_out:
                            self.compress_stream(f_in, f_out)

                        # Then encrypt
                        with open(temp_gz_path, "rb") as f_in, open(gzip_encrypted_json_path, "wb") as f_out:
                            self.encrypt_stream(f_in, f_out, encryption_password)

                        output_files.append(gzip_encrypted_json_path)
                    except Exception as e:
                        self.logger.error(f"Error creating compressed and encrypted JSON: {e}")

        # XML format with similar optimizations
        if "xml" in formats:
            if is_chunk:
                xml_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.xml")
                with open(xml_path, "w") as f:
                    self.format_xml(bundles, stream=f)
            else:
                xml_path = os.path.join(output_dir, "patients.xml")

                # Check if the dataset is large enough to warrant streaming
                if len(bundles) > 1000:
                    with open(xml_path, "w") as f:
                        self.format_xml(bundles, stream=f)
                else:
                    # Small dataset, use in-memory processing
                    xml_data = self.format_xml(bundles)
                    if isinstance(xml_data, str):
                        with open(xml_path, "w") as f:
                            f.write(xml_data)
                    else:
                        # This case should ideally not be reached if len(bundles) <= 1000
                        self.logger.warning("xml_data was not a string for small dataset XML processing.")

            output_files.append(xml_path)

            # Compressed XML with streaming
            if use_compression:
                if is_chunk:
                    gzip_xml_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.xml.gz")
                else:
                    gzip_xml_path = os.path.join(output_dir, "patients.xml.gz")

                with open(xml_path, "rb") as f_in, open(gzip_xml_path, "wb") as f_out:
                    self.compress_stream(f_in, f_out)

                output_files.append(gzip_xml_path)

            # Encrypted XML with streaming
            if use_encryption and encryption_password:
                if is_chunk:
                    encrypted_xml_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.xml.enc")
                else:
                    encrypted_xml_path = os.path.join(output_dir, "patients.xml.enc")

                with open(xml_path, "rb") as f_in, open(encrypted_xml_path, "wb") as f_out:
                    self.encrypt_stream(f_in, f_out, encryption_password)

                output_files.append(encrypted_xml_path)

                # Compressed and encrypted XML
                if use_compression:
                    if is_chunk:
                        gzip_encrypted_xml_path = os.path.join(output_dir, f"patients_chunk_{chunk_index}.xml.gz.enc")
                    else:
                        gzip_encrypted_xml_path = os.path.join(output_dir, "patients.xml.gz.enc")

                    # Create temporary compressed file
                    temp_gz_path = self._create_temp_file(suffix=".xml.gz")

                    try:
                        # First compress
                        with open(xml_path, "rb") as f_in, open(temp_gz_path, "wb") as f_out:
                            self.compress_stream(f_in, f_out)

                        # Then encrypt
                        with open(temp_gz_path, "rb") as f_in, open(gzip_encrypted_xml_path, "wb") as f_out:
                            self.encrypt_stream(f_in, f_out, encryption_password)

                        output_files.append(gzip_encrypted_xml_path)
                    except Exception as e:
                        self.logger.error(f"Error creating compressed and encrypted XML: {e}")

        # Create sample NDEF files only for the first chunk, not for appends
        if not is_chunk and bundles:
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
                # Note: NDEF payload for binary data should be bytes directly
                gzip_ndef = self.format_ndef(gzipped_data, "gzip")  # format_ndef expects data, not a dict
                gzip_ndef_path = os.path.join(output_dir, "sample_gzip.ndef.bin")
                with open(gzip_ndef_path, "wb") as f:
                    # Assuming format_ndef returns a dict, we'd serialize its payload if it's binary
                    # However, the current format_ndef is simplified. For binary, we write the payload.
                    if isinstance(gzip_ndef, dict) and "payload" in gzip_ndef:
                        f.write(gzip_ndef["payload"])
                    else:  # If it's raw bytes
                        f.write(gzipped_data)  # Write the actual gzipped data
                output_files.append(gzip_ndef_path)

            # Encrypted NDEF
            if use_encryption and encryption_password:
                encrypted_data = self.encrypt_aes(sample_json.encode("utf-8"), encryption_password)
                encrypted_ndef = self.format_ndef(encrypted_data, "encrypted")  # Pass raw encrypted bytes
                encrypted_ndef_path = os.path.join(output_dir, "sample_encrypted.ndef.bin")
                with open(encrypted_ndef_path, "wb") as f:
                    if isinstance(encrypted_ndef, dict) and "payload" in encrypted_ndef:
                        f.write(encrypted_ndef["payload"])
                    else:  # If it's raw bytes
                        f.write(encrypted_data)  # Write the actual encrypted data
                output_files.append(encrypted_ndef_path)

                # Gzipped and encrypted NDEF
                if use_compression:
                    gzipped_json_bytes = self.compress_gzip(sample_json)  # Ensure this is bytes
                    gzip_encrypted_data = self.encrypt_aes(gzipped_json_bytes, encryption_password)
                    gzip_encrypted_ndef = self.format_ndef(gzip_encrypted_data, "gzip_encrypted")  # Pass raw
                    gzip_encrypted_ndef_path = os.path.join(output_dir, "sample_gzip_encrypted.ndef.bin")
                    with open(gzip_encrypted_ndef_path, "wb") as f:
                        if isinstance(gzip_encrypted_ndef, dict) and "payload" in gzip_encrypted_ndef:
                            f.write(gzip_encrypted_ndef["payload"])
                        else:  # If it's raw bytes
                            f.write(gzip_encrypted_data)  # Write the actual gzip_encrypted_data
                    output_files.append(gzip_encrypted_ndef_path)

        return output_files
