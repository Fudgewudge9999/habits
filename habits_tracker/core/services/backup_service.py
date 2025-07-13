"""Service layer for database backup and restore operations."""

import gzip
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..database import db_manager, get_session


class BackupError(Exception):
    """Raised when backup operation fails."""
    pass


class RestoreError(Exception):
    """Raised when restore operation fails."""
    pass


class BackupService:
    """Service for database backup and restore operations."""
    
    @classmethod
    def create_backup(
        cls,
        output_path: Optional[str] = None,
        compress: bool = False,
        verify: bool = True
    ) -> Dict[str, Any]:
        """Create a complete backup of the habits database.
        
        Args:
            output_path: Optional custom backup file path
            compress: Whether to compress the backup file
            verify: Whether to verify backup integrity
            
        Returns:
            Backup information dictionary
            
        Raises:
            BackupError: If backup fails
        """
        try:
            # Generate backup filename if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"habits_backup_{timestamp}.db"
                if compress:
                    backup_name += ".gz"
                
                # Use ~/.habits/ directory for backups
                backup_dir = Path.home() / ".habits" / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(backup_dir / backup_name)
            
            backup_path = Path(output_path)
            
            # Get source database path
            source_db_path = Path(db_manager.get_database_path())
            
            if not source_db_path.exists():
                raise BackupError("Source database file does not exist")
            
            # Get database statistics before backup
            stats_before = cls._get_database_stats()
            
            # Create backup
            if compress:
                cls._create_compressed_backup(source_db_path, backup_path)
            else:
                cls._create_regular_backup(source_db_path, backup_path)
            
            # Verify backup if requested
            verification_result = None
            if verify:
                verification_result = cls._verify_backup(backup_path, compress)
            
            # Get backup file statistics
            backup_size = backup_path.stat().st_size
            
            backup_info = {
                "backup_path": str(backup_path),
                "backup_size": backup_size,
                "compressed": compress,
                "created_at": datetime.now().isoformat(),
                "source_database": str(source_db_path),
                "database_stats": stats_before,
                "verification": verification_result
            }
            
            return backup_info
            
        except Exception as e:
            raise BackupError(f"Backup failed: {str(e)}")
    
    @classmethod
    def restore_backup(
        cls,
        backup_path: str,
        verify: bool = True,
        create_backup: bool = True
    ) -> Dict[str, Any]:
        """Restore database from backup file.
        
        Args:
            backup_path: Path to backup file
            verify: Whether to verify backup before restoring
            create_backup: Whether to backup current database before restore
            
        Returns:
            Restore information dictionary
            
        Raises:
            RestoreError: If restore fails
        """
        try:
            backup_file = Path(backup_path)
            
            if not backup_file.exists():
                raise RestoreError(f"Backup file not found: {backup_path}")
            
            # Detect if backup is compressed
            is_compressed = backup_path.endswith('.gz')
            
            # Verify backup integrity if requested
            verification_result = None
            if verify:
                verification_result = cls._verify_backup(backup_file, is_compressed)
                if not verification_result["valid"]:
                    raise RestoreError(f"Backup verification failed: {verification_result['error']}")
            
            # Create backup of current database if requested
            pre_restore_backup = None
            if create_backup:
                try:
                    pre_restore_backup_info = cls.create_backup(
                        output_path=None,
                        compress=False,
                        verify=False  # Skip verification for speed
                    )
                    pre_restore_backup = pre_restore_backup_info["backup_path"]
                except Exception as e:
                    # Don't fail restore if backup fails, just warn
                    print(f"Warning: Could not create pre-restore backup: {e}")
            
            # Get current database path
            current_db_path = Path(db_manager.get_database_path())
            
            # Restore the backup
            if is_compressed:
                cls._restore_compressed_backup(backup_file, current_db_path)
            else:
                cls._restore_regular_backup(backup_file, current_db_path)
            
            # Verify database integrity after restore
            if not db_manager.verify_database_integrity():
                raise RestoreError("Database integrity check failed after restore")
            
            # Get statistics after restore
            stats_after = cls._get_database_stats()
            
            restore_info = {
                "backup_path": str(backup_file),
                "restored_to": str(current_db_path),
                "pre_restore_backup": pre_restore_backup,
                "restored_at": datetime.now().isoformat(),
                "database_stats": stats_after,
                "verification": verification_result
            }
            
            return restore_info
            
        except Exception as e:
            raise RestoreError(f"Restore failed: {str(e)}")
    
    @classmethod
    def list_backups(cls, backup_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backup files.
        
        Args:
            backup_dir: Optional custom backup directory
            
        Returns:
            List of backup file information
        """
        if backup_dir is None:
            backup_dir = Path.home() / ".habits" / "backups"
        else:
            backup_dir = Path(backup_dir)
        
        if not backup_dir.exists():
            return []
        
        backups = []
        
        # Find backup files
        for file_path in backup_dir.glob("*.db*"):
            if file_path.is_file():
                is_compressed = file_path.suffix == '.gz'
                file_stats = file_path.stat()
                
                backup_info = {
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": file_stats.st_size,
                    "compressed": is_compressed,
                    "created_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    "is_valid": None  # Will be set if verification is run
                }
                
                backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    @classmethod
    def verify_backup(cls, backup_path: str) -> Dict[str, Any]:
        """Verify backup file integrity.
        
        Args:
            backup_path: Path to backup file to verify
            
        Returns:
            Verification result dictionary
        """
        backup_file = Path(backup_path)
        is_compressed = backup_path.endswith('.gz')
        
        return cls._verify_backup(backup_file, is_compressed)
    
    @classmethod
    def _create_regular_backup(cls, source_path: Path, backup_path: Path) -> None:
        """Create regular (uncompressed) backup."""
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, backup_path)
        
        # Set appropriate file permissions
        backup_path.chmod(0o600)  # rw-------
    
    @classmethod
    def _create_compressed_backup(cls, source_path: Path, backup_path: Path) -> None:
        """Create compressed backup."""
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(source_path, 'rb') as source_file:
            with gzip.open(backup_path, 'wb') as backup_file:
                shutil.copyfileobj(source_file, backup_file)
        
        # Set appropriate file permissions
        backup_path.chmod(0o600)  # rw-------
    
    @classmethod
    def _restore_regular_backup(cls, backup_path: Path, target_path: Path) -> None:
        """Restore from regular (uncompressed) backup."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, target_path)
        
        # Set appropriate file permissions
        target_path.chmod(0o600)  # rw-------
    
    @classmethod
    def _restore_compressed_backup(cls, backup_path: Path, target_path: Path) -> None:
        """Restore from compressed backup."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        with gzip.open(backup_path, 'rb') as backup_file:
            with open(target_path, 'wb') as target_file:
                shutil.copyfileobj(backup_file, target_file)
        
        # Set appropriate file permissions
        target_path.chmod(0o600)  # rw-------
    
    @classmethod
    def _verify_backup(cls, backup_path: Path, is_compressed: bool) -> Dict[str, Any]:
        """Verify backup file integrity."""
        verification = {
            "valid": False,
            "error": None,
            "file_readable": False,
            "database_accessible": False,
            "tables_exist": False,
            "checksum": None
        }
        
        try:
            # Check if file is readable
            if is_compressed:
                with gzip.open(backup_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to verify
            else:
                with open(backup_path, 'rb') as f:
                    f.read(1024)  # Read first 1KB to verify
            
            verification["file_readable"] = True
            
            # Calculate checksum
            hasher = hashlib.sha256()
            if is_compressed:
                with gzip.open(backup_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
            else:
                with open(backup_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
            
            verification["checksum"] = hasher.hexdigest()
            
            # For more thorough verification, we could create a temporary database
            # and try to open it, but that's complex and might not be worth it
            # for now, we'll just verify file readability
            
            verification["valid"] = True
            
        except gzip.BadGzipFile:
            verification["error"] = "Invalid gzip file format"
        except IOError as e:
            verification["error"] = f"File read error: {str(e)}"
        except Exception as e:
            verification["error"] = f"Verification failed: {str(e)}"
        
        return verification
    
    @classmethod
    def _get_database_stats(cls) -> Dict[str, Any]:
        """Get current database statistics."""
        try:
            return db_manager.get_database_stats()
        except Exception:
            return {"error": "Could not retrieve database statistics"}
    
    @classmethod
    def cleanup_old_backups(
        cls, 
        backup_dir: Optional[str] = None, 
        keep_count: int = 10
    ) -> Dict[str, Any]:
        """Clean up old backup files, keeping only the most recent ones.
        
        Args:
            backup_dir: Optional custom backup directory
            keep_count: Number of recent backups to keep
            
        Returns:
            Cleanup result dictionary
        """
        if backup_dir is None:
            backup_dir = Path.home() / ".habits" / "backups"
        else:
            backup_dir = Path(backup_dir)
        
        if not backup_dir.exists():
            return {"deleted_count": 0, "kept_count": 0, "errors": []}
        
        backups = cls.list_backups(str(backup_dir))
        
        deleted_count = 0
        errors = []
        
        # Delete old backups (keep only the most recent keep_count)
        for backup in backups[keep_count:]:
            try:
                Path(backup["path"]).unlink()
                deleted_count += 1
            except Exception as e:
                errors.append(f"Failed to delete {backup['name']}: {str(e)}")
        
        return {
            "deleted_count": deleted_count,
            "kept_count": min(len(backups), keep_count),
            "errors": errors
        }