messages:
	xgettext -a -d jose --files-from=POTFILES.in --from-code=UTF-8 --directory=..

pofiles:
	msginit --locale=pt --input=jose.po -o en/LC_MESSAGES/pt.po
	msginit --locale=en --input=jose.po -o en/LC_MESSAGES/en.po

mofiles:
	msgfmt -o en/LC_MESSAGES/pt.mo pt/LC_MESSAGES/pt.po
	msgfmt -o en/LC_MESSAGES/en.mo en/LC_MESSAGES/en.po

poclear:
	rm *.po
	rm */*.po

moclear:
	rm */*.mo

clearall:
	rm *.po
	rm */*.po
	rm */*.mo
