CC       = g++
CMPFLAGS = -O2 -g
BSTFLAGS = -lboost_system -lboost_filesystem -lboost_program_options -lboost_thread
UHDFLAGS = -luhd
OBJFILES = radar.o xmit.o recv.o util.o signal.o
TARGET   = radar

all: $(TARGET)

$(TARGET): $(OBJFILES)
	$(CC) -o $@ $^ $(BSTFLAGS) $(UHDFLAGS)

%.o: %.cpp
	$(CC) -o $@ $^ -c $(CMPFLAGS)

clean:
	rm -f $(OBJFILES) $(TARGET)

