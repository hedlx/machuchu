from OpenGL import GL

# Pyopengl shader compilation errors are unreadable, so we'll define our own
# routine.


class ShaderCompilationError(Exception):
    def __init__(self, text):
        super().__init__("Shader compile failure")
        self.text = text


def compileShader(source, shaderType):
    shader = GL.glCreateShader(shaderType)
    GL.glShaderSource(shader, [source.encode()])
    GL.glCompileShader(shader)
    result = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
    if not (result):
        raise ShaderCompilationError(GL.glGetShaderInfoLog(shader).decode())
    return shader
