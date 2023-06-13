from OpenGL import GL

# Pyopengl shader compilation errors are unreadable, so we'll define our own
# routine.


class ShaderCompilationError(Exception):
    def __init__(self, text: str) -> None:
        super().__init__(f"Shader compile failure:\n{text}")
        self.text = text


def compileShader(source: str, shaderType: GL.GLenum) -> GL.GLuint:
    shader = GL.glCreateShader(shaderType)
    GL.glShaderSource(shader, [source.encode()])
    GL.glCompileShader(shader)
    result = GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS)
    if not (result):
        raise ShaderCompilationError(GL.glGetShaderInfoLog(shader).decode())
    return shader
