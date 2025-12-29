"""Integration tests for dev-start application."""
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
from src.detector import TechnologyDetector, Technology
from src.proxy_manager import ProxyManager
from src.env_manager import EnvironmentManager


class TestIntegrationDetectorWithEnvManager(unittest.TestCase):
    """Integration tests for Detector and EnvManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.detector = TechnologyDetector()
        self.env_manager = EnvironmentManager(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_detect_java_and_create_config(self):
        """Test detecting Java project and creating configuration."""
        # Create pom.xml
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('''
        <project>
            <properties>
                <java.version>17</java.version>
            </properties>
            <dependencies>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter</artifactId>
                </dependency>
            </dependencies>
        </project>
        ''')

        # Detect technology
        technology = self.detector.detect(self.temp_dir)
        self.assertEqual(technology, Technology.JAVA_SPRINGBOOT)

        # Create environment configuration
        self.env_manager.create_env_file({
            'JAVA_HOME': 'C:\\Program Files\\Java\\jdk-17',
            'MAVEN_HOME': 'C:\\tools\\maven',
            'SPRING_PROFILES_ACTIVE': 'dev'
        })

        env_file = self.temp_dir / '.env'
        self.assertTrue(env_file.exists())

        content = env_file.read_text()
        self.assertIn('JAVA_HOME', content)
        self.assertIn('MAVEN_HOME', content)
        self.assertIn('SPRING_PROFILES_ACTIVE', content)

    def test_detect_python_and_create_venv_config(self):
        """Test detecting Python project and creating virtual environment config."""
        # Create requirements.txt
        req_file = self.temp_dir / 'requirements.txt'
        req_file.write_text('flask==2.3.0\nrequests==2.31.0\n')

        # Detect technology
        technology = self.detector.detect(self.temp_dir)
        self.assertEqual(technology, Technology.PYTHON)

        # Create Python environment configuration
        self.env_manager.create_env_file({
            'PYTHONPATH': str(self.temp_dir),
            'FLASK_APP': 'app.py',
            'FLASK_ENV': 'development'
        })

        # Create config directory
        config_dir = self.env_manager.create_config_dir('config')
        self.assertTrue(config_dir.exists())

        # Write a config file
        self.env_manager.write_config_file(
            'settings.py',
            'DEBUG = True\nSECRET_KEY = "dev"\n',
            'config'
        )

        settings_file = self.temp_dir / 'config' / 'settings.py'
        self.assertTrue(settings_file.exists())

    def test_detect_nodejs_and_create_env(self):
        """Test detecting Node.js project and creating environment."""
        # Create package.json
        package_json = self.temp_dir / 'package.json'
        package_json.write_text('''
        {
            "name": "test-app",
            "version": "1.0.0",
            "engines": {
                "node": ">=20.0.0"
            }
        }
        ''')

        # Detect technology
        technology = self.detector.detect(self.temp_dir)
        self.assertEqual(technology, Technology.NODEJS)

        # Create Node.js environment
        self.env_manager.create_env_file({
            'NODE_ENV': 'development',
            'PORT': '3000',
            'API_URL': 'http://localhost:3000/api'
        })

        env_file = self.temp_dir / '.env'
        content = env_file.read_text()
        self.assertIn('NODE_ENV=development', content)
        self.assertIn('PORT=3000', content)


class TestIntegrationProxyWithDownload(unittest.TestCase):
    """Integration tests for Proxy and Download functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.proxy_manager = ProxyManager()

    def tearDown(self):
        """Clean up proxy settings."""
        self.proxy_manager.clear_proxy()

    def test_proxy_configuration_flow(self):
        """Test complete proxy configuration flow."""
        # Step 1: Configure proxy
        http_proxy = 'http://proxy.company.com:8080'
        https_proxy = 'http://proxy.company.com:8443'

        self.proxy_manager.set_proxy(
            http_proxy=http_proxy,
            https_proxy=https_proxy
        )

        # Step 2: Verify proxy is set in manager
        self.assertEqual(self.proxy_manager.http_proxy, http_proxy)
        self.assertEqual(self.proxy_manager.https_proxy, https_proxy)

        # Step 3: Get proxy dict for requests
        proxy_dict = self.proxy_manager.get_proxy_dict()
        self.assertEqual(proxy_dict['http'], http_proxy)
        self.assertEqual(proxy_dict['https'], https_proxy)

        # Step 4: Clear proxy
        self.proxy_manager.clear_proxy()
        self.assertEqual(self.proxy_manager.get_proxy_dict(), {})


class TestIntegrationFullWorkflow(unittest.TestCase):
    """Integration tests for full workflow scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_java_project_setup_workflow(self):
        """Test complete Java project setup workflow."""
        # Create Java/Spring Boot project structure
        (self.temp_dir / 'src' / 'main' / 'java').mkdir(parents=True)
        (self.temp_dir / 'src' / 'main' / 'resources').mkdir(parents=True)

        # Create pom.xml with spring-boot dependency
        pom_file = self.temp_dir / 'pom.xml'
        pom_file.write_text('''
        <project>
            <properties>
                <java.version>17</java.version>
            </properties>
            <dependencies>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter</artifactId>
                </dependency>
            </dependencies>
        </project>
        ''')

        # Detect technology
        detector = TechnologyDetector()
        technology = detector.detect(self.temp_dir)
        self.assertEqual(technology, Technology.JAVA_SPRINGBOOT)

        # Setup environment
        env_manager = EnvironmentManager(self.temp_dir)
        env_manager.create_env_file({
            'JAVA_HOME': 'C:\\jdk-17',
            'SPRING_PROFILES_ACTIVE': 'dev'
        })

        # Create application.properties
        env_manager.write_config_file(
            'application.properties',
            'server.port=8080\nspring.datasource.url=jdbc:h2:mem:testdb\n',
            'src/main/resources'
        )

        # Verify everything is created
        self.assertTrue((self.temp_dir / '.env').exists())
        self.assertTrue((self.temp_dir / 'src' / 'main' / 'resources' / 'application.properties').exists())

    def test_python_project_setup_workflow(self):
        """Test complete Python project setup workflow."""
        # Create Python project structure
        (self.temp_dir / 'src').mkdir()
        (self.temp_dir / 'tests').mkdir()

        # Create requirements.txt
        req_file = self.temp_dir / 'requirements.txt'
        req_file.write_text('flask==2.3.0\npytest==7.4.0\n')

        # Detect technology
        detector = TechnologyDetector()
        technology = detector.detect(self.temp_dir)
        self.assertEqual(technology, Technology.PYTHON)

        # Setup environment
        env_manager = EnvironmentManager(self.temp_dir)
        env_manager.create_env_file({
            'PYTHONPATH': str(self.temp_dir / 'src'),
            'FLASK_APP': 'app.py',
            'ENV': 'development'
        })

        # Create pytest configuration
        env_manager.write_config_file(
            'pytest.ini',
            '[pytest]\ntestpaths = tests\n'
        )

        # Verify setup
        self.assertTrue((self.temp_dir / '.env').exists())
        self.assertTrue((self.temp_dir / 'pytest.ini').exists())

    def test_nodejs_project_setup_workflow(self):
        """Test complete Node.js project setup workflow."""
        # Create Node.js project structure
        (self.temp_dir / 'src').mkdir()
        (self.temp_dir / 'public').mkdir()

        # Create package.json
        package_json = self.temp_dir / 'package.json'
        package_json.write_text('''
        {
            "name": "my-app",
            "version": "1.0.0",
            "main": "src/index.js",
            "engines": {
                "node": ">=18.0.0"
            }
        }
        ''')

        # Detect technology
        detector = TechnologyDetector()
        technology = detector.detect(self.temp_dir)
        self.assertEqual(technology, Technology.NODEJS)

        # Setup environment
        env_manager = EnvironmentManager(self.temp_dir)
        env_manager.create_env_file({
            'NODE_ENV': 'development',
            'PORT': '3000',
            'DATABASE_URL': 'mongodb://localhost:27017/myapp'
        })

        # Verify setup
        self.assertTrue((self.temp_dir / '.env').exists())
        env_content = (self.temp_dir / '.env').read_text()
        self.assertIn('PORT=3000', env_content)


if __name__ == '__main__':
    unittest.main()
