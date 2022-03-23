var nextBackgroundId = 1;
var currentBackgroundId = 0;

var color_x = [0.0, 0.1, 0.5];
var color_y = [0.8, 0.0, 0.8];

setupBackground(currentBackgroundId);
window.addEventListener("resize", () => {
    var ourBackgroundId = nextBackgroundId++;
    currentBackgroundId = ourBackgroundId;
    setTimeout(() => {
        setupBackground(ourBackgroundId);
    }, 100);
});

var img = document.getElementById("album_art");
img.crossOrigin = "Anonymous";

function update_colors(color_x_new, color_y_new) {
  color_x = color_x_new;
  color_y = color_y_new;

  setupBackground(currentBackgroundId);
}

img.addEventListener('load', function() {
    var v = new Vibrant(img);

    if (typeof v.VibrantSwatch !== "undefined" && typeof v.DarkVibrantSwatch !== "undefined")
    {
        album_color_1 = v.VibrantSwatch.rgb;
        album_color_2 = v.DarkVibrantSwatch.rgb;

        album_color_1[0] = album_color_1[0] / 255.0;
        album_color_1[1] = album_color_1[1] / 255.0;
        album_color_1[2] = album_color_1[2] / 255.0;

        album_color_2[0] = album_color_2[0] / 255.0;
        album_color_2[1] = album_color_2[1] / 255.0;
        album_color_2[2] = album_color_2[2] / 255.0;

        if (album_color_1[0] != color_x[0] && album_color_1[1] != color_x[1] && album_color_1[2] != color_x[2] && album_color_2[0] != color_y[0] && album_color_2[1] != color_y[1] && album_color_2[2] != color_y[2])
        {
            update_colors(album_color_1, album_color_2);
        }
    }
}
);

function setupBackground(ourBackgroundId) {
    if (currentBackgroundId !== ourBackgroundId) {
        return;
    }

    var prevCanvas = document.getElementById("blob-canvas");
    if (prevCanvas) {
        prevCanvas.remove();
    }

    var canvas = document.createElement("canvas");
    canvas.id = "blob-canvas";
    var mouse = { x: 0, y: 0 };

    canvas.onmousemove = function (e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    }

    var width = canvas.width = window.innerWidth;
    var height = canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    var gl = canvas.getContext('webgl');

    var numMetaballs = 30;
    var metaballs = [];

    for (var i = 0; i < numMetaballs; i++) {
        var radius = Math.random() * 60 + 10;
        metaballs.push({
            x: Math.random() * (width - 2 * radius) + radius,
            y: Math.random() * (height - 2 * radius) + radius,
            vx: (Math.random() - 0.5) * 3,
            vy: (Math.random() - 0.5) * 3,
            r: radius * 0.75
        });
    }

    var vertexShaderSrc = `
attribute vec2 position;

void main() {
// position specifies only x and y.
// We set z to be 0.0, and w to be 1.0
gl_Position = vec4(position, 0.0, 1.0);
}
`;

    var fragmentShaderSrc = `
precision highp float;

const float WIDTH = ` + (width >> 0) + `.0;
const float HEIGHT = ` + (height >> 0) + `.0;

uniform vec3 metaballs[` + numMetaballs + `];

void main(){
float x = gl_FragCoord.x;
float y = gl_FragCoord.y;

float sum = 0.0;
for (int i = 0; i < ` + numMetaballs + `; i++) {
vec3 metaball = metaballs[i];
float dx = metaball.x - x;
float dy = metaball.y - y;
float radius = metaball.z;

sum += (radius * radius) / (dx * dx + dy * dy);
}

if (sum >= 0.99) {
  float x_per = x / WIDTH;
  float y_per = 1.0 - (y / HEIGHT);
  vec3 color_x = vec3(${color_x[0]}, ${color_x[1]}, ${color_x[2]});
  vec3 color_y = vec3(${color_y[0]}, ${color_y[1]}, ${color_y[2]});
  gl_FragColor = vec4(x_per*color_x + y_per*color_y, 1.0);
  return;
}

gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);
}

`;

    var vertexShader = compileShader(vertexShaderSrc, gl.VERTEX_SHADER);
    var fragmentShader = compileShader(fragmentShaderSrc, gl.FRAGMENT_SHADER);

    var program = gl.createProgram();
    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);
    gl.useProgram(program);

    var vertexData = new Float32Array([
        -1.0, 1.0, // top left
        -1.0, -1.0, // bottom left
        1.0, 1.0, // top right
        1.0, -1.0, // bottom right
    ]);
    var vertexDataBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexDataBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, vertexData, gl.STATIC_DRAW);

    var positionHandle = getAttribLocation(program, 'position');
    gl.enableVertexAttribArray(positionHandle);
    gl.vertexAttribPointer(positionHandle,
        2, // position is a vec2
        gl.FLOAT, // each component is a float
        gl.FALSE, // don't normalize values
        2 * 4, // two 4 byte float components per vertex
        0 // offset into each span of vertex data
    );

    var metaballsHandle = getUniformLocation(program, 'metaballs');

    loop();
    function loop() {
        if (currentBackgroundId !== ourBackgroundId) {
            return;
        }
        for (var i = 0; i < numMetaballs; i++) {
            var metaball = metaballs[i];
            metaball.x += metaball.vx;
            metaball.y += metaball.vy;

            if (metaball.x < metaball.r || metaball.x > width - metaball.r) metaball.vx *= -1;
            if (metaball.y < metaball.r || metaball.y > height - metaball.r) metaball.vy *= -1;
        }

        var dataToSendToGPU = new Float32Array(3 * numMetaballs);
        for (var i = 0; i < numMetaballs; i++) {
            var baseIndex = 3 * i;
            var mb = metaballs[i];
            dataToSendToGPU[baseIndex + 0] = mb.x;
            dataToSendToGPU[baseIndex + 1] = mb.y;
            dataToSendToGPU[baseIndex + 2] = mb.r;
        }
        gl.uniform3fv(metaballsHandle, dataToSendToGPU);

        //Draw
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        requestAnimationFrame(loop);
    }

    function compileShader(shaderSource, shaderType) {
        var shader = gl.createShader(shaderType);
        gl.shaderSource(shader, shaderSource);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            throw "Shader compile failed with: " + gl.getShaderInfoLog(shader);
        }

        return shader;
    }

    function getUniformLocation(program, name) {
        var uniformLocation = gl.getUniformLocation(program, name);
        if (uniformLocation === -1) {
            throw 'Can not find uniform ' + name + '.';
        }
        return uniformLocation;
    }

    function getAttribLocation(program, name) {
        var attributeLocation = gl.getAttribLocation(program, name);
        if (attributeLocation === -1) {
            throw 'Can not find attribute ' + name + '.';
        }
        return attributeLocation;
    }
}
