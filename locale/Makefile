messages:
	xgettext --files-from=POTFILES.in -d jose --from-code=UTF-8 \
		--keyword=say --directory=..
	python3 po2json.py jose.po > jose.json
	rm jose.po
