SRC=$(wildcard src/*.py)
CORE=$(wildcard core/*.py)
WEB=$(wildcard web/*)

SRC_MPY=$(SRC:%.py=build/%.mpy)
CORE_MPY=$(CORE:%.py=build/%.mpy)

AMPY_PORT=COM3

.PHONY:

defaut:
	echo $(SRC)

	
compile: compile-src compile-core
deploy: deploy-src deploy-core deploy-web deploy-main
clean: clean-deploy clean-compile

compile-src: $(SRC_MPY)
deploy-src: $(SRC_MPY:.mpy=.mpy.deployed)
redeploy-src: $(SRC_MPY)
	ampy put $^ $(dir $<)
	for f in $^; do touch $f.deployed; done
	
deploy-main:
	ampy put main.py .

compile-core: $(CORE_MPY)
deploy-core: $(CORE_MPY:.mpy=.mpy.deployed)

deploy-web: $(WEB:%=build/%.deployed)

deploy-dirs: build/dirs.deployed
dirs.deployed:
	ampy mkdir --exists-okay src
	ampy mkdir --exists-okay web
	ampy mkdir --exists-okay core
	touch build/dirs.deployed

build/%.mpy: %.py
	mkdir -p `dirname $@`
	mpy-cross -v -march=xtensawin $^ -o $@ 


build/%.deployed: % deploy-dirs
	ampy put $< $(dir $<)
	mkdir -p `dirname $@`
	touch $@
	
clean-deploy:
	rm $(SRC_MPY:.mpy=.mpy.deployed) -f
	rm $(CORE_MPY:.mpy=.mpy.deployed) -f
	rm $(WEB:%=build/%.deployed) -f
	rm build/dirs.deployed -f
    
clean-compile:
	rm $(SRC_MPY) -f
	rm $(CORE_MPY) -f

erase-vfs:
	esptool.exe -p $(AMPY_PORT) --chip esp32 erase_region 0x310000 0xF0000
