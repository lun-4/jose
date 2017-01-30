messages:
	xgettext -a -d jose --files-from=POTFILES.in --from-code=UTF-8 --directory=..

pofiles:
	msginit --locale=pt --input=jose.po -o jose/pt.po
	msginit --locale=en --input=jose.po -o jose/en.po

mofiles:
	msgfmt -o jose/en.mo en.po
	msgfmt -o jose/pt.mo pt.po

poclear:
	rm *.po
	rm jose/*.po

clear:
	rm jose/en.mo
