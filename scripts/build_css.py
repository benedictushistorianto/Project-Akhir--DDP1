"""Build app.css: modern-normalize reset + custom CSS dari input.css."""
import pathlib

input_css = pathlib.Path("static/css/input.css").read_text(encoding="utf-8")

RESET = """/* Preflight Reset (setara Tailwind Preflight v4, inline) */
/*! modern-normalize v3.0 | MIT | sindresorhus/modern-normalize */
*,::after,::before{box-sizing:border-box}
html{-moz-tab-size:4;tab-size:4;-webkit-text-size-adjust:100%;line-height:1.15}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif,"Apple Color Emoji","Segoe UI Emoji"}
hr{height:0;color:inherit}
abbr[title]{text-decoration:underline dotted}
b,strong{font-weight:bolder}
code,kbd,pre,samp{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",Menlo,monospace;font-size:1em}
small{font-size:80%}
sub,sup{font-size:75%;line-height:0;position:relative;vertical-align:baseline}
sub{bottom:-.25em}sup{top:-.5em}
table{text-indent:0;border-color:inherit}
button,input,optgroup,select,textarea{font-family:inherit;font-size:100%;line-height:1.15;margin:0}
button,select{text-transform:none}
button{-webkit-appearance:button}
::-moz-focus-inner{border-style:none;padding:0}
:-moz-focusring{outline:1px dotted ButtonText}
:-moz-ui-invalid{box-shadow:none}
legend{padding:0}
progress{vertical-align:baseline}
::-webkit-inner-spin-button,::-webkit-outer-spin-button{height:auto}
[type=search]{-webkit-appearance:textfield;outline-offset:-2px}
::-webkit-search-decoration{-webkit-appearance:none}
::-webkit-file-upload-button{-webkit-appearance:button;font:inherit}
summary{display:list-item}
blockquote,dl,dd,h1,h2,h3,h4,h5,h6,hr,figure,p,pre{margin:0}
fieldset{margin:0;padding:0}
ol,ul,menu{list-style:none;margin:0;padding:0}
textarea{resize:vertical}
input::placeholder,textarea::placeholder{opacity:1;color:#9ca3af}
button,[role=button]{cursor:pointer}
img,svg,video,canvas,audio,iframe,embed,object{display:block;vertical-align:middle}
img,video{max-width:100%;height:auto}
[hidden]{display:none}
"""

output = input_css.replace('@import "tailwindcss";', RESET, 1)

pathlib.Path("static/css/app.css").write_text(output, encoding="utf-8")
print(f"app.css written: {len(output)} bytes")
