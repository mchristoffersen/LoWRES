CC       = g++
CMPFLAGS = -O2 -g
BSTFLAGS = -lboost_system -lboost_filesystem -lboost_program_options -lboost_thread
UHDFLAGS = -luhd
OBJFILES = radar.o xmit.o recv.o util.o signal.o socket.o
HDRFILES = xmit.h recv.h util.h signal.h socket.h
TARGET   = ../radar

all: $(TARGET)

$(TARGET): $(OBJFILES)
	$(CC) -o $@ $^ $(BSTFLAGS) $(UHDFLAGS)
	rm $(OBJFILES)

%.o: %.cpp %.h
	$(CC) -o $@ $< -c $(CMPFLAGS)

clean:
	rm -f $(OBJFILES) $(TARGET)

