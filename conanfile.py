from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration
import os


class LibsshConan(ConanFile):
    name = "libssh"
    description = "libssh is a multiplatform C library implementing the SSHv2 protocol on client and server side"
    homepage = "https://www.libssh.org/"    
    license = "LGPL"
    url = "https://github.com/Infactum/conan-libssh"
    topics = ("libssh", "ssh", "shell", "ssh2", "connection")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_zlib": [True, False],
        "crypto_backend": ["openssl", "mbedtls"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_zlib": True,
        "crypto_backend": "openssl",
    }
    generators = "cmake"
    _source_subfolder = "source_subfolder"

    def requirements(self):
        if self.options.with_zlib:
            self.requires("zlib/1.2.11")
        if self.options.crypto_backend == "openssl":
            self.requires("openssl/1.1.1f")
        elif self.options.crypto_backend == "mbedtls":
            self.requires("mbedtls/2.16.3-gpl")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("libssh-%s" % (self.version), self._source_subfolder)
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "set(APPLICATION_NAME ${PROJECT_NAME})",
                              '''set(APPLICATION_NAME ${PROJECT_NAME})
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()''')

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions['WITH_ZLIB'] = self.options.with_zlib
        if self.options.crypto_backend == "openssl":
            pass
        elif self.options.crypto_backend == "mbedtls":
            cmake.definitions['WITH_MBEDTLS'] = True
        else:
            raise ConanInvalidConfiguration("Crypto backend must be specified")

        cmake.definitions['WITH_EXAMPLES'] = False
        cmake.definitions['UNIT_TESTING'] = False
        cmake.definitions['CLIENT_TESTING'] = False
        cmake.definitions['SERVER_TESTING'] = False
        cmake.definitions['WITH_NACL'] = False
        cmake.definitions['UNIT_TESTING'] = False

        cmake.configure(source_folder=self._source_subfolder)
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy("COPYING", dst="licenses",
                  src=self._source_subfolder, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["ssh"]

        if not self.options.shared:
            self.cpp_info.defines.append("LIBSSH_STATIC")

        if self.settings.compiler == "Visual Studio" and not self.options.shared:
            self.cpp_info.system_libs.append('ws2_32')
            self.cpp_info.defines.append("WIN32_LEAN_AND_MEAN")
        elif self.settings.os == "Linux":
            self.cpp_info.system_libs.extend(['pthread', 'dl'])
