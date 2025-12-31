"""Performance tests for dev-start."""
import pytest
import unittest
import time
import tempfile
import shutil
from pathlib import Path
from src.detector import TechnologyDetector, Technology
from src.env_manager import EnvironmentManager
from src.proxy_manager import ProxyManager


@pytest.mark.performance
class TestPerformance(unittest.TestCase):
    """Performance tests to ensure operations complete in acceptable time."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.detector = TechnologyDetector()
        self.env_manager = EnvironmentManager(self.temp_dir)
        self.proxy_manager = ProxyManager()

    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @pytest.mark.performance
    def test_technology_detection_speed(self):
        """Test that technology detection completes quickly."""
        # Create test files
        (self.temp_dir / 'pom.xml').write_text('<project>spring-boot</project>')
        (self.temp_dir / 'requirements.txt').write_text('flask==2.0.0')
        (self.temp_dir / 'package.json').write_text('{"name": "test"}')

        # Measure detection time
        iterations = 100
        start_time = time.time()

        for _ in range(iterations):
            self.detector.detect(self.temp_dir)

        elapsed = time.time() - start_time
        avg_time = elapsed / iterations

        # Should detect in less than 10ms on average
        self.assertLess(
            avg_time,
            0.01,
            f"Detection should average <10ms, got {avg_time*1000:.2f}ms"
        )

        print(f"\nDetection performance: {avg_time*1000:.2f}ms average over {iterations} iterations")

    @pytest.mark.performance
    def test_env_file_creation_speed(self):
        """Test that environment file creation is fast."""
        variables = {f'VAR_{i}': f'value_{i}' for i in range(100)}

        iterations = 50
        start_time = time.time()

        for i in range(iterations):
            test_dir = self.temp_dir / f'test_{i}'
            test_dir.mkdir()
            env_manager = EnvironmentManager(test_dir)
            env_manager.create_env_file(variables)

        elapsed = time.time() - start_time
        avg_time = elapsed / iterations

        # Should create env file in less than 15ms on average (relaxed for CI)
        self.assertLess(
            avg_time,
            0.015,
            f"Env creation should average <15ms, got {avg_time*1000:.2f}ms"
        )

        print(f"\nEnv creation performance: {avg_time*1000:.2f}ms average over {iterations} iterations")

    @pytest.mark.performance
    def test_proxy_configuration_speed(self):
        """Test that proxy configuration is instantaneous."""
        iterations = 1000
        start_time = time.time()

        for _ in range(iterations):
            proxy = ProxyManager()
            proxy.set_proxy(
                http_proxy='http://proxy:8080',
                https_proxy='http://proxy:8080'
            )
            proxy.get_proxy_dict()
            proxy.clear_proxy()

        elapsed = time.time() - start_time
        avg_time = elapsed / iterations

        # Should configure proxy in less than 1ms on average
        self.assertLess(
            avg_time,
            0.001,
            f"Proxy config should average <1ms, got {avg_time*1000:.2f}ms"
        )

        print(f"\nProxy config performance: {avg_time*1000:.2f}ms average over {iterations} iterations")

    @pytest.mark.performance
    def test_directory_creation_speed(self):
        """Test that directory creation is fast."""
        iterations = 100
        start_time = time.time()

        for i in range(iterations):
            env_manager = EnvironmentManager(self.temp_dir / f'proj_{i}')
            env_manager.create_config_dir(f'config/nested/deep/level_{i}')

        elapsed = time.time() - start_time
        avg_time = elapsed / iterations

        # Should create nested directories in less than 10ms on average (relaxed for CI)
        self.assertLess(
            avg_time,
            0.010,
            f"Directory creation should average <10ms, got {avg_time*1000:.2f}ms"
        )

        print(f"\nDirectory creation performance: {avg_time*1000:.2f}ms average over {iterations} iterations")

    @pytest.mark.performance
    def test_file_detection_patterns_speed(self):
        """Test speed of file pattern detection."""
        # Create various project files
        (self.temp_dir / 'pom.xml').write_text('<project></project>')
        (self.temp_dir / 'build.gradle').write_text('plugins {}')
        (self.temp_dir / 'requirements.txt').write_text('')
        (self.temp_dir / 'setup.py').write_text('')
        (self.temp_dir / 'package.json').write_text('{}')
        (self.temp_dir / 'yarn.lock').write_text('')

        iterations = 1000
        start_time = time.time()

        for _ in range(iterations):
            files = [f.name for f in self.temp_dir.iterdir() if f.is_file()]
            _ = any(f in files for f in ['pom.xml', 'build.gradle'])
            _ = any(f in files for f in ['requirements.txt', 'setup.py'])
            _ = any(f in files for f in ['package.json', 'yarn.lock'])

        elapsed = time.time() - start_time
        avg_time = elapsed / iterations

        # Should detect patterns in less than 2ms on average (relaxed for CI)
        self.assertLess(
            avg_time,
            0.002,
            f"Pattern detection should average <2ms, got {avg_time*1000:.2f}ms"
        )

        print(f"\nPattern detection performance: {avg_time*1000:.2f}ms average over {iterations} iterations")

    @pytest.mark.performance
    def test_memory_efficiency_large_env_files(self):
        """Test memory efficiency with large environment files."""
        # Create large environment file
        large_env = {f'VARIABLE_{i}': f'value_{i}' * 100 for i in range(1000)}

        start_time = time.time()
        self.env_manager.create_env_file(large_env)
        elapsed = time.time() - start_time

        # Should handle large env file in less than 50ms
        self.assertLess(
            elapsed,
            0.05,
            f"Large env file should be created in <50ms, got {elapsed*1000:.2f}ms"
        )

        # Verify file was created correctly
        env_file = self.temp_dir / '.env'
        self.assertTrue(env_file.exists())

        # Verify content
        content = env_file.read_text()
        self.assertIn('VARIABLE_0', content)
        self.assertIn('VARIABLE_999', content)

        print(f"\nLarge env file ({len(large_env)} variables) created in {elapsed*1000:.2f}ms")


def run_performance_tests():
    """Run performance tests and print summary."""
    print("\n" + "=" * 70)
    print("PERFORMANCE TEST SUITE")
    print("=" * 70)

    pytest.main([__file__, '-v', '-m', 'performance', '-s'])


if __name__ == '__main__':
    run_performance_tests()
