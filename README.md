# vasiniyo-media-loader

`vasiniyo-media-loader`- Linux CLI util for downloading `YouTube` videos as `MP3`, based on `yt-dlp`.

In the root directory there is a launcher script `./vas-yt`,<br>
which allows running the application both locally and inside a Docker container.

```
Usage: vas-yt --output <output_dir> (--link <name> | --links <file>) [OPTION]...

Options:
  -o, --output <output_dir> output directory
      --link <name>         youtube link
      --links <file>        file with youtube links
  -r, --runtime             runtime mode (default: docker)
  -b, --build               rebuild docker container
      --stop                stop docker container
      --debug               debug mode
  -q, --quiet               quiet mode
  -h, --help                display this help and exit

Examples:
  vas-yt \
    --output out \
    --link https://www.youtube.com/watch?v=dQw4w9WgXcQ \
    --runtime docker
  vas-yt -o out --links path/to/links.txt -q --runtime local
```

## Installation
Install `Docker` for your system: https://docs.docker.com/get-started/get-docker/.<br>
Or install the required dependencies:
- `Python 3.11+`
- `Deno`
- `ffmpeg` + `ffprobe`

## Usage
**Currently, the tool works only if the Brave browser is installed<br>
and you are logged into a YouTube account!**

By default, a Docker image named `vasiniyo-media-loader:latest` will be created.<br>
Use the `--runtime local` flag if you don't want to run util inside a container.<br>
Use the `-q` flag if you want to display only processed URLs with their status.<br>
`logs/` - directory where logs are stored.<br>
`ytloads/` - directory where downloaded files are saved.<br>

## Contributing

Contributions are welcome.

You can:
- Open existing issues
- Suggest new issues
- Submit pull requests with improvements

Please open a new issue if you find a bug or have a feature request.
