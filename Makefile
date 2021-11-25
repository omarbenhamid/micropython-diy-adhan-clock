SRC=$(wildcard src/*.py)
CORE=$(wildcard core/*.py)
WEB=$(web/*)
AMPY_PORT=COM3

.PHONY:

defaut:
	echo $(SRC)

	
compile: compile-src compile-core
deploy: deploy-src deploy-core deploy-weba
clean: clean-deploy clean-compile

compile-src: $(SRC:.py=.mpy)
deploy-src: $(SRC:.py=.mpy.deployed)
redeploy-src: $(SRC:.py=.mpy)
	ampy put $^ $(dir $<)
	for f in $^; do touch $f.deployed; done
	

compile-core: $(CORE:.py=.mpy)
deploy-core: $(CORE:.py=.mpy.deployed)

deploy-web: $(SRC:=.deployed)

deploy-dirs: dirs.deployed
dirs.deployed:
	ampy mkdir --exists-okay src
	ampy mkdir --exists-okay web
	ampy mkdir --exists-okay core
	touch dirs.deployed

%.mpy: %.py
	mpy-cross -v -march=xtensawin $^ -o $@ 


%.deployed: % deploy-dirs
	ampy put $< $(dir $<)
	touch $@
	
clean-deploy:
	rm $(SRC:.py=.mpy.deployed) -f
	rm $(CORE:.py=.mpy.deployed) -f
	rm $(WEB:=.deployed) -f
	rm dirs.deployed
    
clean-compile:
	rm $(SRC:.py=.mpy) -f
	rm $(CORE:.py=.mpy) -f
