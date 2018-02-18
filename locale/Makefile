messages:
	xgettext --files-from=POTFILES.in -d jose --from-code=UTF-8 \
		--keyword=say --directory=..
	python3 po2json.py jose.po > jose.json
	rm jose.po

merges:
	python3 json-merge.py jose.json jose.en.json > jose.en2.json
	rm jose.en.json
	mv jose.en2.json jose.en.json

	python3 json-merge.py jose.json jose.pt.json > jose.pt2.json
	rm jose.pt.json
	mv jose.pt2.json jose.pt.json
