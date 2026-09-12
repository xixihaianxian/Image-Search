-- folder table
create table folders(
    id integer primary key ,
    folder_path varchar(300) not null unique ,
    name varchar(100) not null,
    -- 目录的标识符，作为缩略图存放的目录的名称
    indicate varchar(200) not null unique
);

-- image table
create table images(
    id integer primary key ,
    folder_id integer not null ,
    -- 原始图片地址
    path varchar(300) not null unique ,
    -- 原始图片名称
    name varchar(100) not null  ,
    -- 图片拓展名
    extension varchar(50) not null ,
    -- 缩略图存放的路径
    thumbnail_path varchar(300) not null unique ,
    created_at datetime default current_timestamp,
    updated_at datetime default current_timestamp,
    constraint folders_images_folder_id foreign key (folder_id) references folders(id) on delete cascade on update cascade
);
-- images name index
create index index_name on images(name);
-- images folder id index
create index index_folder_index on images(folder_id);

PRAGMA foreign_keys = ON;

-- imagefeatures table
create table if not exists imagefeatures(
    id integer primary key ,
    model varchar(200) not null ,
    path varchar(300) not null  ,
    feature varchar(300) not null unique,
    constraint images_imagefeatures_path foreign key (path) references images(path) on update cascade on delete cascade,
    constraint model_path_unique unique (model,path)
);

-- models table
create table if not exists models(
    id integer primary key ,
    model varchar(200) not null unique
);

insert into models(model) values ('vgg16');

insert into models(model) values ('openclip');