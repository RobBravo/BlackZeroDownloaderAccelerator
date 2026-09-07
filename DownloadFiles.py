import sys

from blackzero.cli import main as cli_main


def run(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        print("🚀 Acelerador de descargas BlackZero")
        print("#####################################\n")
        arguments = [input("🔗 Ingrese la URL del archivo a descargar: ").strip()]
    return cli_main(arguments)


if __name__ == "__main__":
    raise SystemExit(run())
