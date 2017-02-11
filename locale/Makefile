messages:
	xgettext --files-from=POTFILES.in -d jose --from-code=UTF-8 \
		--keyword=say --directory=..
	python3 po2json.py jose.po > jose.json
	rm jose.po

pofiles:
	mkdir -p pt/LC_MESSAGES
	msginit --locale=pt --input=jose.po -o pt/LC_MESSAGES/pt.po

	mkdir -p en/LC_MESSAGES
	msginit --locale=en --input=jose.po -o en/LC_MESSAGES/en.po

mofiles:
	msgfmt -o pt/LC_MESSAGES/pt.mo pt/LC_MESSAGES/pt.po
	msgfmt -o en/LC_MESSAGES/en.mo en/LC_MESSAGES/en.po

poclear:
	rm *.po

moclear:
	rm */*.mo

clearall:
	rm -f *.po
	rm -f */LC_MESSAGES/*.po
	rm -f */LC_MESSAGES/*.mo
	rm jose.json
