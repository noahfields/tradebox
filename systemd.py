import os
import glob
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)


def install_systemd_services(src_dir=None, dest_dir="/etc/systemd/system", overwrite=False):
	"""
	Copy all `.service` files from `src_dir` to `dest_dir`.

	Defaults:
	- `src_dir`: the sibling `systemd` directory next to this module (i.e. `src/systemd`).
	- `dest_dir`: `/etc/systemd/system`.

	Parameters:
	- `overwrite` (bool): if True, overwrite existing files in `dest_dir`.

	Returns a list of destination file paths that were copied.

	Raises FileNotFoundError if the source directory doesn't exist, and
	PermissionError if writing to the destination fails due to permissions.
	"""
	if src_dir is None:
		src_dir = os.path.join(os.path.dirname(__file__), "systemd")

	if not os.path.isdir(src_dir):
		raise FileNotFoundError(f"source directory not found: {src_dir}")

	#os.makedirs(dest_dir, exist_ok=True)

	pattern = os.path.join(src_dir, "*.service")
	service_files = glob.glob(pattern)
	copied = []

	for src in service_files:
		basename = os.path.basename(src)
		dst = os.path.join(dest_dir, basename)

		if os.path.exists(dst) and not overwrite:
			logger.debug("Skipping existing service file: %s", dst)
			continue

		try:
			#shutil.copy2(src, dst)
			subprocess.run(f"sudo cp {src} {dst}", shell=True)
			try:
				os.chmod(dst, 0o644)
			except Exception:
				logger.debug("Could not set permissions on %s", dst)
			copied.append(dst)
			logger.info("Copied service: %s -> %s", src, dst)
		except PermissionError as e:
			raise PermissionError(f"Insufficient permissions to write to {dest_dir}: {e}")
		except Exception as e:
			logger.error("Failed to copy %s to %s: %s", src, dst, e)
			raise

	return copied


# create function to delete systemd services listed in src/systemd from /etc/systemd/system


def remove_systemd_services(src_dir=None, dest_dir="/etc/systemd/system"):
	"""
	Delete all `.service` files in `dest_dir` that correspond to files in `src_dir`.

	Defaults:
	- `src_dir`: the sibling `systemd` directory next to this module (i.e. `src/systemd`).
	- `dest_dir`: `/etc/systemd/system`.

	Parameters:
	- `reload_daemon` (bool): if True, run `systemctl daemon-reload` after removals.

	Returns a list of destination file paths that were removed.

	Raises FileNotFoundError if the source directory doesn't exist, and
	PermissionError if removing files fails due to permissions.
	"""
	if src_dir is None:
		src_dir = os.path.join(os.path.dirname(__file__), "systemd")

	if not os.path.isdir(src_dir):
		raise FileNotFoundError(f"source directory not found: {src_dir}")

	pattern = os.path.join(src_dir, "*.service")
	src_files = glob.glob(pattern)
	removed = []

	for src in src_files:
		basename = os.path.basename(src)
		dst = os.path.join(dest_dir, basename)

		if not os.path.exists(dst):
			logger.debug("Service file not present, skipping: %s", dst)
			continue

		try:
			# Use sudo to attempt removal, mirroring install behavior which used sudo cp
			subprocess.run(f"sudo rm -f {dst}", shell=True, check=True)
			removed.append(dst)
			logger.info("Removed service: %s", dst)
		except subprocess.CalledProcessError as e:
			# Likely a permission issue or command failure
			logger.error("Failed to remove %s: %s", dst, e)
			# Inspect returncode/message to decide whether to raise PermissionError
			raise PermissionError(f"Insufficient permissions to remove {dst}: {e}")
		except PermissionError:
			raise
		except Exception as e:
			logger.error("Unexpected error removing %s: %s", dst, e)
			raise

	# if reload_daemon and removed:
	# 	try:
	# 		subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
	# 	except subprocess.CalledProcessError as e:
	# 		logger.debug("Could not reload systemd daemon: %s", e)

	return removed


# create a function to enable the services listed in src/systemd that are present in /etc/systemd/system


def enable_systemd_services(src_dir=None, dest_dir="/etc/systemd/system", reload_daemon=True):
	"""
	Enable (and optionally start) all `.service` units in `dest_dir` that correspond
	to files in `src_dir`.

	Defaults:
	- `src_dir`: the sibling `systemd` directory next to this module (i.e. `src/systemd`).
	- `dest_dir`: `/etc/systemd/system`.

	Parameters:
	- `start` (bool): if True, also run `systemctl start` for each enabled unit.
	- `reload_daemon` (bool): if True, run `systemctl daemon-reload` after enabling.

	Returns a list of unit names that were enabled.

	Raises FileNotFoundError if the source directory doesn't exist, and
	PermissionError if enabling fails due to permissions.
	"""
	if src_dir is None:
		src_dir = os.path.join(os.path.dirname(__file__), "systemd")

	if not os.path.isdir(src_dir):
		raise FileNotFoundError(f"source directory not found: {src_dir}")

	pattern = os.path.join(src_dir, "*.service")
	src_files = glob.glob(pattern)
	enabled = []

	for src in src_files:
		basename = os.path.basename(src)
		if not basename.endswith(".service"):
			continue

		unit = basename
		dst = os.path.join(dest_dir, basename)

		if not os.path.exists(dst):
			logger.debug("Service file not present in %s, skipping: %s", dest_dir, dst)
			continue

		try:
			subprocess.run(f"sudo systemctl enable {unit}", shell=True, check=True)
			enabled.append(unit)
			logger.info("Enabled service: %s", unit)
		except subprocess.CalledProcessError as e:
			logger.error("Failed to enable %s: %s", unit, e)
			raise PermissionError(f"Failed to enable {unit}: {e}")
		except PermissionError:
			raise
		except Exception as e:
			logger.error("Unexpected error enabling %s: %s", unit, e)
			raise

	return enabled


# create function to disable all services listed in src/systemd that are in /etc/systemd/system


def disable_systemd_services(src_dir=None, dest_dir="/etc/systemd/system"):
	"""
	Disable all `.service` units in `dest_dir` that correspond to files in `src_dir`.

	Defaults:
	- `src_dir`: the sibling `systemd` directory next to this module (i.e. `src/systemd`).
	- `dest_dir`: `/etc/systemd/system`.

	Parameters:
	- `reload_daemon` (bool): if True, run `systemctl daemon-reload` after disabling.

	Returns a list of unit names that were disabled.

	Raises FileNotFoundError if the source directory doesn't exist, and
	PermissionError if disabling fails due to permissions.
	"""
	if src_dir is None:
		src_dir = os.path.join(os.path.dirname(__file__), "systemd")

	if not os.path.isdir(src_dir):
		raise FileNotFoundError(f"source directory not found: {src_dir}")

	pattern = os.path.join(src_dir, "*.service")
	src_files = glob.glob(pattern)
	disabled = []

	for src in src_files:
		basename = os.path.basename(src)
		if not basename.endswith(".service"):
			continue

		unit = basename
		dst = os.path.join(dest_dir, basename)

		if not os.path.exists(dst):
			logger.debug("Service file not present in %s, skipping: %s", dest_dir, dst)
			continue

		try:
			subprocess.run(f"sudo systemctl disable {unit}", shell=True, check=True)
			disabled.append(unit)
			logger.info("Disabled service: %s", unit)
		except subprocess.CalledProcessError as e:
			logger.error("Failed to disable %s: %s", unit, e)
			raise PermissionError(f"Failed to disable {unit}: {e}")
		except PermissionError:
			raise
		except Exception as e:
			logger.error("Unexpected error disabling %s: %s", unit, e)
			raise

	# if reload_daemon and disabled:
	# 	try:
	# 		subprocess.run("sudo systemctl daemon-reload", shell=True, check=True)
	# 	except subprocess.CalledProcessError as e:
	# 		logger.debug("Could not reload systemd daemon: %s", e)

	return disabled


def start_systemd_services(src_dir=None, dest_dir="/etc/systemd/system", restart=False):
	"""
	Start (or optionally restart) all `.service` units in `dest_dir` that correspond
	to files in `src_dir`.

	Defaults:
	- `src_dir`: the sibling `systemd` directory next to this module (i.e. `src/systemd`).
	- `dest_dir`: `/etc/systemd/system`.

	Parameters:
	- `restart` (bool): if True, run `systemctl restart` instead of `start`.

	Returns a list of unit names that were started/restarted.

	Raises FileNotFoundError if the source directory doesn't exist, and
	PermissionError if starting fails due to permissions.
	"""
	if src_dir is None:
		src_dir = os.path.join(os.path.dirname(__file__), "systemd")

	if not os.path.isdir(src_dir):
		raise FileNotFoundError(f"source directory not found: {src_dir}")

	pattern = os.path.join(src_dir, "*.service")
	src_files = glob.glob(pattern)
	started = []

	for src in src_files:
		basename = os.path.basename(src)
		if not basename.endswith(".service"):
			continue

		unit = basename
		dst = os.path.join(dest_dir, basename)

		if not os.path.exists(dst):
			logger.debug("Service file not present in %s, skipping: %s", dest_dir, dst)
			continue

		try:
			action = "restart" if restart else "start"
			subprocess.run(f"sudo systemctl {action} {unit}", shell=True, check=True)
			started.append(unit)
			logger.info("%s service: %s", action.capitalize(), unit)
		except subprocess.CalledProcessError as e:
			logger.error("Failed to %s %s: %s", action, unit, e)
			raise PermissionError(f"Failed to {action} {unit}: {e}")
		except PermissionError:
			raise
		except Exception as e:
			logger.error("Unexpected error %sing %s: %s", action, unit, e)
			raise

	return started


def stop_systemd_services(src_dir=None, dest_dir="/etc/systemd/system"):
	"""
	Stop all `.service` units in `dest_dir` that correspond to files in `src_dir`.

	Defaults:
	- `src_dir`: the sibling `systemd` directory next to this module (i.e. `src/systemd`).
	- `dest_dir`: `/etc/systemd/system`.

	Returns a list of unit names that were stopped.

	Raises FileNotFoundError if the source directory doesn't exist, and
	PermissionError if stopping fails due to permissions.
	"""
	if src_dir is None:
		src_dir = os.path.join(os.path.dirname(__file__), "systemd")

	if not os.path.isdir(src_dir):
		raise FileNotFoundError(f"source directory not found: {src_dir}")

	pattern = os.path.join(src_dir, "*.service")
	src_files = glob.glob(pattern)
	stopped = []

	for src in src_files:
		basename = os.path.basename(src)
		if not basename.endswith(".service"):
			continue

		unit = basename
		dst = os.path.join(dest_dir, basename)

		if not os.path.exists(dst):
			logger.debug("Service file not present in %s, skipping: %s", dest_dir, dst)
			continue

		try:
			subprocess.run(f"sudo systemctl stop {unit}", shell=True, check=True)
			stopped.append(unit)
			logger.info("Stopped service: %s", unit)
		except subprocess.CalledProcessError as e:
			logger.error("Failed to stop %s: %s", unit, e)
			raise PermissionError(f"Failed to stop {unit}: {e}")
		except PermissionError:
			raise
		except Exception as e:
			logger.error("Unexpected error stopping %s: %s", unit, e)
			raise

	return stopped

