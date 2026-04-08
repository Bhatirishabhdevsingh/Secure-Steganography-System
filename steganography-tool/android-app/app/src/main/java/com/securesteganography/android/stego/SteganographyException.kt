package com.securesteganography.android.stego

open class SteganographyException(message: String) : RuntimeException(message)

class CapacityException(message: String) : SteganographyException(message)

class InvalidImageException(message: String) : SteganographyException(message)

class AuthenticationException(message: String) : SteganographyException(message)
