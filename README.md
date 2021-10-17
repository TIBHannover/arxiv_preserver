<div align="center">    
 
# TIB-arXiv: An Alternative Search Portal for the arXiv Pre-print Server  
</div>

> Matthias Springstein, Huu Hung Nguyen, Anett Hoppe, Ralph Ewerth:
"TIB-arXiv: An Alternative Search Portal for the arXiv Pre-print Server".
In: *International Conference on Theory and Practice of Digital Libraries (TPDL)*, Porto, Springer, 2018, 295-298.


## Run your own version

In order to run your own version of this software, we recommend using the docker-compose scripts provided with the project.

```
sudo docker compose up
```

After the first start the SQL database must be created with the following command:

```
sudo docker compose exec arxiv python3 manage.py migrate --noinput  
```


## Fetch new informations from ArXiv.org
To load the current papers from arxiv.org you can use the following command. This script is not suitable for downloading the entire collection ([bulk](https://arxiv.org/help/bulk_data_s3))

```
sudo docker compose exec arxiv python3 manage.py update --output /media --from 2021-10-15
sudo docker compose exec arxiv python3 manage.py indexing_es
```