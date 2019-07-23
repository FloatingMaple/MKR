import argparse
import numpy as np

RATING_FILE_NAME = dict({'movie': 'ratings.dat',
                         'book': 'BX-Book-Ratings.csv',
                         'music': 'user_artists.dat',
                         'news': 'ratings.txt'})
SEP = dict({'movie': '::', 'book': ';', 'music': '\t', 'news': '\t'})
THRESHOLD = dict({'movie': 4, 'book': 0, 'music': 0, 'news': 0})


def read_item_index_to_entity_id_file():
    # 读取物品id-实体id文件
    file = './data/' + DATASET + '/item_index2entity_id.txt'
    print('reading item index to entity id file: ' + file + ' ...')
    i = 0
    for line in open(file, encoding='utf-8').readlines():
        # .strip() 返回原序列的副本，移除指定的开头和末尾字节,如果省略参数，默认移除ASCII空白符
        # item_index 物品ID
        item_index = line.strip().split('\t')[0]
        # satori_id 实体ID
        satori_id = line.strip().split('\t')[1]
        item_index_old2new[item_index] = i
        entity_id2index[satori_id] = i
        i += 1


def convert_rating():
    # 转换评分矩阵
    file = './data/' + DATASET + '/' + RATING_FILE_NAME[DATASET]

    print('reading rating file ...')
    # 物品集，item_index_old2new.values() 应该是从0开始到物品的个数-1（movie:2347个）
    item_set = set(item_index_old2new.values())
    # 用户积极/消极评分
    user_pos_ratings = dict()
    user_neg_ratings = dict()

    # [1:] 跳过第一行 （有的数据集第一行是说明）
    for line in open(file, encoding='utf-8').readlines()[1:]:
        # 不同的数据集有不同的间隔符,取得去掉间隔符之后的数据
        array = line.strip().split(SEP[DATASET])

        # remove prefix and suffix quotation marks for BX dataset
        # 删除BSX数据集的前缀和后缀引导
        if DATASET == 'book':
            # map() 会根据提供的函数对指定序列做映射。第一个参数 function 以参数序列中的每一个元素调用 function 函数，返回包含每次 function 函数返回值的新列表。
            # lambda 代表一个匿名函数
            # x[1:-1] 是数组的切片用法，从索引值为1到-1的切片出来（-1即倒数第一个）(即去头去尾),e.g. [0,1,2,3,4]->[1,2,3]
            array = list(map(lambda x: x[1:-1], array))

        # 从评分中读取到的物品信息(movie:电影原编号; book:书籍ISBN; music:音乐家原ID)
        item_index_old = array[1]
        if item_index_old not in item_index_old2new:  # the item is not in the final item set
            continue
        item_index = item_index_old2new[item_index_old]

        # 从评分中读取到的用户id信息
        user_index_old = int(array[0])

        # 从评分中读取到的评分信息
        rating = float(array[2])
        # 判断门槛，movie中>=4分的归为积极
        if rating >= THRESHOLD[DATASET]:
            if user_index_old not in user_pos_ratings:
                # 一开始时使用set()创建空集合,{}用来创建空字典。
                user_pos_ratings[user_index_old] = set()
            user_pos_ratings[user_index_old].add(item_index)
        else:
            if user_index_old not in user_neg_ratings:
                user_neg_ratings[user_index_old] = set()
            user_neg_ratings[user_index_old].add(item_index)

    print('converting rating file ...')
    # 创建处理后的评分文件
    writer = open('../data/' + DATASET + '/ratings_final.txt', 'w', encoding='utf-8')
    user_cnt = 0
    user_index_old2new = dict()
    for user_index_old, pos_item_set in user_pos_ratings.items():
        if user_index_old not in user_index_old2new:
            user_index_old2new[user_index_old] = user_cnt
            user_cnt += 1
        user_index = user_index_old2new[user_index_old]

        for item in pos_item_set:
            writer.write('%d\t%d\t1\n' % (user_index, item))
        unwatched_set = item_set - pos_item_set
        if user_index_old in user_neg_ratings:
            unwatched_set -= user_neg_ratings[user_index_old]
        # 从不可见集合中随机选取同样大小的负例
        for item in np.random.choice(list(unwatched_set), size=len(pos_item_set), replace=False):
            writer.write('%d\t%d\t0\n' % (user_index, item))
    writer.close()
    print('number of users: %d' % user_cnt)
    print('number of items: %d' % len(item_set))


def convert_kg():
    print('converting kg.txt file ...')
    entity_cnt = len(entity_id2index)
    relation_cnt = 0

    writer = open('../data/' + DATASET + '/kg_final.txt', 'w', encoding='utf-8')
    file = open('../data/' + DATASET + '/kg.txt', encoding='utf-8')

    for line in file:
        array = line.strip().split('\t')
        head_old = array[0]
        relation_old = array[1]
        tail_old = array[2]

        if head_old not in entity_id2index:
            continue
        head = entity_id2index[head_old]

        if tail_old not in entity_id2index:
            entity_id2index[tail_old] = entity_cnt
            entity_cnt += 1
        tail = entity_id2index[tail_old]

        if relation_old not in relation_id2index:
            relation_id2index[relation_old] = relation_cnt
            relation_cnt += 1
        relation = relation_id2index[relation_old]

        writer.write('%d\t%d\t%d\n' % (head, relation, tail))

    writer.close()
    print('number of entities (containing items): %d' % entity_cnt)
    print('number of relations: %d' % relation_cnt)


if __name__ == '__main__':
    np.random.seed(555)
# argparse模块用于编写命令行接口
    # 1. 创建一个解析器对象
    parser = argparse.ArgumentParser()
    # 2. 添加参数
    parser.add_argument('-d', type=str, default='movie', help='which dataset to preprocess')
    # 3. 解析解析器中保存的参数
    args = parser.parse_args()
    DATASET = args.d

    entity_id2index = dict()
    relation_id2index = dict()
    item_index_old2new = dict()

    # 几个转换操作，对评分文件、kg文件做处理，可以消去其中的间隔，减小矩阵大小
    read_item_index_to_entity_id_file()
    convert_rating()
    convert_kg()

    print('done')
