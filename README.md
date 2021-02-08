# Photostore

Photo archive for adelante.cu

## development

Requires Python 3, node 12 and yarn

```bash
git clone https://github.com/ybenitezf/photostore
cd photostore
python3 -m venv env
. env/bin/activate
make dev
```

And run database migrations `flask db upgrade -d photostore/migrations` or `flask deploy db-upgrade`

## tests

```bash
make test
```

Or with coverage

```bash
make coverage
```

## Generating distribution archives

```bash
make dist
```

## Install

REVIEW THIS

```bash
pip install https://github.com/ybenitezf/photostore/archive/master.tar.gz
```
