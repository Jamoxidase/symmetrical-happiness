import os
import re
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from datetime import datetime
import logging
from abc import ABC
import resource
from contextlib import contextmanager
import tempfile
import shutil


RETAIN_OUTPUT_FILES = False
TOOLS_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))


class ToolManager(ABC):
    """Abstract base class for tRNA analysis tools with enhanced security."""
    
    def __init__(self, work_dir: str, enable_logging: bool = False):
        # Use absolute paths for Heroku deployment
        self.work_dir = Path('/app/trnaChat/tools')
        self.data_dir = self.work_dir / 'data'
        self.logs_dir = self.data_dir / 'logs'
        self.results_dir = self.data_dir / 'results'
        
        # Validate and create directories
        for directory in [self.data_dir, self.logs_dir, self.results_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.addHandler(logging.NullHandler())

    def validate_work_path(self, path: Union[str, Path]) -> Path:
        """Validate paths within work directory"""
        full_path = Path(path).resolve()
        if not full_path.is_relative_to(self.work_dir):
            raise ValueError(f"Path escapes work directory: {path}")
        return full_path

    @contextmanager
    def working_directory(self, path: Path):
        """Safely change working directory"""
        original_dir = Path.cwd()
        try:
            os.chdir(path)
            yield
        finally:
            os.chdir(original_dir)
    
    def _run_command(self, cmd: list, tool_name: str) -> Dict[str, str]:
        """Execute a command with enhanced security measures."""
        print(f"\nRunning {tool_name}...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        stdout_file = self.logs_dir / f'{tool_name}-stdout-{timestamp}.log'
        stderr_file = self.logs_dir / f'{tool_name}-stderr-{timestamp}.log'
        
        # Only validate paths that should be within work directory
        # BUT skip the executable (first command)
        cmd = [
            str(arg) if i == 0 else  # Don't validate the executable path
            (str(self.validate_work_path(str(arg))) 
            if (Path(str(arg)).is_absolute() and 
                any(str(arg).startswith(str(d)) for d in [self.work_dir, self.data_dir, self.logs_dir, self.results_dir]))
            else str(arg)) 
            for i, arg in enumerate(cmd)
        ]
        
        self.logger.info(f"Running command: {' '.join(cmd)}")
        self.logger.info(f"Output files: stdout={stdout_file}, stderr={stderr_file}")
        
        os.umask(0o077)  # Set restrictive umask
        
        try:
            with open(stdout_file, 'w') as stdout_fh, open(stderr_file, 'w') as stderr_fh:
                result = subprocess.run(
                    cmd,
                    stdout=stdout_fh,
                    stderr=stderr_fh,
                    text=True,
                    check=True
                )
            
            return {
                'stdout_file': str(stdout_file),
                'stderr_file': str(stderr_file)
            }
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with return code {e.returncode}")
            with open(stderr_file) as f:
                error_content = f.read()
            raise RuntimeError(f"Command failed: {error_content}")


class TRNAScan(ToolManager):
    """Interface for tRNAscan-SE tool."""
    
    VALID_CLADES = {'Eukaryota', 'Bacteria', 'Archaea'}
    
    def __init__(self, work_dir: str, enable_logging: bool = True):
        super().__init__(work_dir, enable_logging)
        
        # Add extensive path debugging
        print("\n=== Directory Structure Debug ===")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Contents of /app:")
        try:
            print(os.listdir('/app'))
        except Exception as e:
            print(f"Error listing /app: {e}")

        print(f"\nContents of /app/trnaChat if it exists:")
        try:
            print(os.listdir('/app/trnaChat'))
        except Exception as e:
            print(f"Error listing /app/trnaChat: {e}")

        print(f"\nContents of /app/trnaChat/tools if it exists:")
        try:
            print(os.listdir('/app/trnaChat/tools'))
        except Exception as e:
            print(f"Error listing /app/trnaChat/tools: {e}")

        print(f"\nFull path traversal:")
        path_to_check = Path('/app/trnaChat/tools/trna_software/bin/tRNAscan-SE')
        current = Path('/')
        for part in path_to_check.parts[1:]:
            current = current / part
            try:
                print(f"Checking {current}:")
                print(f"Exists: {current.exists()}")
                if current.exists():
                    print(f"Is directory: {current.is_dir()}")
                    print(f"Is file: {current.is_file()}")
                    if current.is_dir():
                        print(f"Contents: {os.listdir(current)}")
            except Exception as e:
                print(f"Error checking {current}: {e}")

        APP_ROOT = Path('/app/trnaChat/tools')
        self.executable = str(APP_ROOT / 'trna_software' / 'bin' / 'tRNAscan-SE')

        print("\n=== Executable Debug ===")
        print(f"APP_ROOT: {APP_ROOT}")
        print(f"Final executable path: {self.executable}")
        try:
            print(f"Executable exists: {Path(self.executable).exists()}")
            print(f"Executable permissions: {oct(Path(self.executable).stat().st_mode)}")
            print(f"Is executable bit set: {os.access(self.executable, os.X_OK)}")
            print(f"Real path: {os.path.realpath(self.executable)}")
        except Exception as e:
            print(f"Error checking executable: {e}")

        if not Path(self.executable).is_file():
            raise FileNotFoundError(f"tRNAscan-SE executable not found at {self.executable}")

    def run_from_sequence(self, sequence: str, clade: str) -> str:
        """
        Run tRNAscan-SE analysis from a sequence string.
        Returns the contents of the .ss file.
        """
        if clade not in self.VALID_CLADES:
            raise ValueError(f"Invalid clade. Must be one of: {self.VALID_CLADES}")
            
        # Create temporary FASTA file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.fa', delete=False) as temp_fasta:
            temp_fasta.write(f">temp_seq\n{sequence}\n")
            temp_fasta_path = temp_fasta.name
            
        try:
            # Run tRNAscan-SE
            output_base = self.results_dir / "temp_output"
            ss_file = str(output_base) + ".ss"  # Convert to string here
            
            cmd = [
                str(self.executable),  # Convert Path to string for command
                '-E' if clade == 'Eukaryota' else '-B' if clade == 'Bacteria' else '-A',
                '-f', ss_file,
                '-o', str(output_base) + ".out",
                '-m', str(output_base) + ".stats",
                '-c', '/app/trnaChat/tools/trna_software/bin/tRNAscan-SE.conf',
                temp_fasta_path
            ]
            
            self._run_command(cmd, "tRNAscan")
            
            # Add debugging for file existence
            print(f"Checking SS file at: {ss_file}")
            print(f"SS file exists: {Path(ss_file).exists()}")
            print(f"Directory contents: {os.listdir(os.path.dirname(ss_file))}")
            
            # Read SS file contents
            with open(ss_file) as f:
                ss_contents = f.read()
                
            return ss_contents
            
        finally:
            # Cleanup only if RETAIN_OUTPUT_FILES is False
            os.unlink(temp_fasta_path)  # Always remove temp input
            if not RETAIN_OUTPUT_FILES:
                for ext in ['.ss', '.out', '.stats']:
                    try:
                        os.unlink(str(output_base) + ext)
                    except FileNotFoundError:
                        pass


class Sprinzl(ToolManager):
    """Interface for tRNA_sprinzl_pos tool."""
    
    VALID_CLADES = {'Eukaryota', 'Bacteria', 'Archaea'}
    
    def __init__(self, work_dir: str, enable_logging: bool = True):
        super().__init__(work_dir, enable_logging)
        
        APP_ROOT = Path('/app/trnaChat/tools')
        self.sprinzl_dir = APP_ROOT / 'trna_software' / 'sprinzl'
        executable_path = self.sprinzl_dir / 'tRNA_sprinzl_pos'  # Keep as Path

        # Add debug logging
        print(f"Looking for Sprinzl at: {executable_path}")
        print(f"APP_ROOT is: {APP_ROOT}")
        print(f"sprinzl_dir is: {self.sprinzl_dir}")
        print(f"Directory contents of {self.sprinzl_dir}: {os.listdir(self.sprinzl_dir)}")

        if not executable_path.is_file():
            raise FileNotFoundError(f"tRNA_sprinzl_pos executable not found at {executable_path}")
            
        self.executable = str(executable_path)  # Convert to string after check

    def run_from_ss(self, ss_content: str, clade: str) -> str:
        """
        Run Sprinzl analysis from SS file contents.
        Returns the contents of the .pos file.
        """
        if clade not in self.VALID_CLADES:
            raise ValueError(f"Invalid clade. Must be one of: {self.VALID_CLADES}")
            
        # Create temporary SS file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ss', delete=False) as temp_ss:
            temp_ss.write(ss_content)
            temp_ss_path = temp_ss.name
            print(f"Created SS file with contents:\n{ss_content}")
            
        try:
            # Create temporary output directory
            temp_output_dir = self.results_dir / f"sprinzl_temp_{datetime.now():%Y%m%d_%H%M%S}"
            temp_output_dir.mkdir(exist_ok=True)
            print(f"Created output directory: {temp_output_dir}")
            
            cmd = [
                str(self.executable),  # Use full path
                '-c', str(self.sprinzl_dir / 'map-sprinzl-pos.conf'),
                '-d', clade,
                '-s', temp_ss_path,
                '-o', str(temp_output_dir)
            ]
            
            print(f"Running Sprinzl command: {' '.join(cmd)}")
            self._run_command(cmd, "Sprinzl")
                
            # Find and read .pos file
            pos_files = list(temp_output_dir.glob("*.pos"))
            print(f"Found POS files: {pos_files}")
            if not pos_files:
                raise RuntimeError("No .pos file generated")
                    
            with open(pos_files[0]) as f:
                pos_contents = f.read()
                print(f"POS file contents:\n{pos_contents}")
                    
            return pos_contents
                
        finally:
            # Cleanup only if RETAIN_OUTPUT_FILES is False
            os.unlink(temp_ss_path)  # Always remove temp input
            if not RETAIN_OUTPUT_FILES:
                shutil.rmtree(temp_output_dir, ignore_errors=True)


class RunPipeline:
    def __init__(self, sequence_cache=None, user_id=None):
        if sequence_cache is None:
            from cache import SequenceCache
            self.sequence_cache = SequenceCache()
        else:
            self.sequence_cache = sequence_cache

        self.user_id = user_id
    
    async def parse_pipeline_request(self, message: str, work_dir: str = "./", enable_logging: bool = True) -> Tuple[str, str]:
        """
        Parse and process a combined tRNAscan-SE/SPRINZL request.
        Returns tuple of (ss_contents, pos_contents)
        Example message:
        tRNAscan-SE/SPRINZL
        Gene Symbol: tRNA-Arg-ACG-1-1
        Clade: Eukaryota
        """
        print("Received Step: ", message)  # debug
        
        # Parse input
        species = None
        if "Homo sapiens" in message:
            species = "human"
            
        gene_symbol_match = re.search(r'Symbol:\s*(\S+)', message)
        clade_match = re.search(r'Clade:\s*(\S+)', message)
        print('hi1')
        if not gene_symbol_match or not clade_match:
            raise ValueError("Message must contain 'Species:' and 'Gene Symbol:' and 'Clade:'")
            
        gene_symbol = gene_symbol_match.group(1)
        clade = clade_match.group(1)
        print('hi')
        sequence_json = self.sequence_cache.get_sequence(species, gene_symbol, self.user_id)
        if not sequence_json:
            return "sequence not found in cache- get sequence", ""
            
        sequence = sequence_json['sequences']['Predicted Mature tRNA']

        print("Sequence: ", sequence)
        
        # Initialize tools, run pipeline
        trnascan = TRNAScan(work_dir, enable_logging)
        ss_contents = trnascan.run_from_sequence(sequence, clade)
        
        # Update tool data with await
        '''await self.sequence_cache.update_tool_data(
            species,
            gene_symbol,
            "trnascan_se_ss",
            ss_contents
        )'''
        
        print("SS Contents: ", ss_contents)

        sprinzl = Sprinzl(work_dir, enable_logging)
        pos_contents = sprinzl.run_from_ss(ss_contents, clade)

        # Update tool data with await
        await self.sequence_cache.update_tool_data(
            species,  # Added missing species parameter
            gene_symbol,
            "sprinzl_pos",
            pos_contents
        )
        
        print("Pos contents: ", pos_contents)  # debug
        return ss_contents, pos_contents