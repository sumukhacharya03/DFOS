#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dirent.h>
#include <fnmatch.h>
void listFiles(const char *dirPath, const char *filter) {
DIR *dir;struct dirent *entry;
dir = opendir(dirPath);
if (dir == NULL) {
perror("Error opening directory");
exit(EXIT_FAILURE);
}
while ((entry = readdir(dir)) != NULL) {
if (fnmatch(filter, entry->d_name, FNM_NOESCAPE) == 0) {
printf("%s/%s\n", dirPath, entry->d_name);
}
}
closedir(dir);
}
int main(int argc, char *argv[]) {
if (argc != 3) {
fprintf(stderr, "Usage: %s <directory> <filename>\n", argv[0]);
return EXIT_FAILURE;
}
const char *dirPath = argv[1];
const char *filter = argv[2];
listFiles(dirPath, filter);
return EXIT_SUCCESS;
}
