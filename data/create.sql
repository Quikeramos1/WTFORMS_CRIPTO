CREATE TABLE "movements" (
	"id"	INTEGER,
	"fecha_actual"	TEXT NOT NULL,
	"hora_actual"	TEXT NOT NULL,
	"tipo_operacion"	TEXT NOT NULL,
	"criptomoneda_origen"	TEXT NOT NULL,
	"cantidad_origen"	REAL NOT NULL,
	"criptomoneda_salida"	TEXT NOT NULL,
	"cantidad_salida"	REAL NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);