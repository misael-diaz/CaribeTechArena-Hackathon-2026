/*

Copyright (c) 2026 Misael Díaz-Maldonado
This source file is released under the MIT License.
See LICENSE file in the project root for the full license information.

*/


#include <stdio.h>
#include <sqlite3.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>

// SQLite ingestion of common products sold at schools
int main() {

	char filename[] = "data/products.txt";
	FILE *filp = fopen(filename, "r");
	if (!filp) {
		if (errno) {
			fprintf(stderr, "%s\n", strerror(errno));
		}
		exit(EXIT_FAILURE);
	}

	int64_t rc = 0;
	sqlite3 *conndb = NULL;
	char const * const namedb = "nutrition.db";
	rc = sqlite3_open(namedb, &conndb);
	if (SQLITE_OK != rc) {
		fprintf(stderr, "%s %s\n", "error: failed to open connection to database:", namedb);
		exit(EXIT_FAILURE);
	}

	char create_table[] = (
		"CREATE TABLE IF NOT EXISTS nutritionfacts ("
		"id INTEGER PRIMARY KEY AUTOINCREMENT,"
		"product_name TEXT UNIQUE,"
		"high_sugar INTEGER,"
		"high_sodium INTEGER,"
		"high_fat INTEGER"
		");"
	);

        char *errmsg = NULL;
        rc = sqlite3_exec(conndb, create_table, NULL, NULL, &errmsg);
	if (SQLITE_OK != rc) {
		fprintf(stderr, "%s", "error: SQL error\n");
		if (errmsg) {
			fprintf(stderr, "%s\n", errmsg);
		}
		sqlite3_close(conndb);
		exit(EXIT_FAILURE);
	}

	// NOTES: strips the new line from product name
	char name[256];
	int status = 0;
	int high_sugar = 0;
	int high_sodium = 0;
	int high_fat = 0;
	int count = 0;
	uint64_t size = 0;
	char *lnp = NULL;
	do {
		if (0 == count) {
			high_sugar = 0;
			high_sodium = 0;
			high_fat = 0;
		}

		errno = 0;
		rc = getline(&lnp, &size, filp);
		if (-1 == rc) {
			if (errno) {
				fprintf(stderr, "%s\n", strerror(errno));
				sqlite3_close(conndb);
				exit(EXIT_FAILURE);
			}
			break;
		} else {
			if (0 == count) {
				lnp[rc - 1] = 0;
				memset(name, 0, sizeof(name));
				strcpy(name, lnp);
			}
			else if (1 == count) {
				status = atoi(lnp);
				high_sugar |= status;
			}
			else if (2 == count) {
				status = atoi(lnp);
				high_sodium |= status;
			}
			else if (3 == count) {
				status = atoi(lnp);
				high_fat |= status;
			}
		}

		++count;

		if (4 == count) {
			char fmt[] = (
				"INSERT OR IGNORE INTO nutritionfacts ("
				"product_name,"
				"high_sugar,"
				"high_sodium,"
				"high_fat) VALUES ("
				"'%s',"
				"%d,"
				"%d,"
				"%d);"
			);
			char sql[4096];
			int bytes_written = snprintf(
				sql,
				4096,
				fmt,
				name,
				high_sugar,
				high_sodium,
				high_fat
			);
			if (bytes_written >= 4096) {
				fprintf(stderr, "%s", "sql truncation error\n");
				sqlite3_close(conndb);
				exit(EXIT_FAILURE);
			}

			int statcode = sqlite3_exec(conndb, sql, NULL, NULL, &errmsg);
			if (SQLITE_OK != statcode) {
				fprintf(stderr, "%s", "error: SQL error\n");
				if (errmsg) {
					fprintf(stderr, "%s\n", errmsg);
				}
				sqlite3_close(conndb);
				exit(EXIT_FAILURE);
			}
		}

		count &= 3;
	} while (rc);

        rc = sqlite3_close(conndb);
	if (SQLITE_OK != rc) {
		fprintf(stderr, "%s %s\n", "error: failed to close connection to database:", namedb);
		exit(EXIT_FAILURE);
	}

	return 0;
}
