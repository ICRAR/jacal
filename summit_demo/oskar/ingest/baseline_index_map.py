import math
import csv
import argparse


def distance_between_points(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the earth in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
        math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * \
        math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = R * c  # Distance in km
    return d


def parse_antenna_file(antenna_file):
    locations = []
    with open(antenna_file) as f:
        for line in f:
            if line.startswith('#'):
                continue
            coord = line.strip('\n')
            if not coord:
                continue
            if ',' in coord:
                coord = coord.split(',')
            else:
                coord = coord.split(' ')

            locations.append((float(coord[1]), float(coord[0])))
    return locations


def generate_baseline_index(positions, exclude_distance, baseline_index_file):
    num_stations = len(positions)

    with open(baseline_index_file, 'w') as index_file:
        index_writer = csv.writer(index_file, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)

        for s1 in range(num_stations):
            for s2 in range(s1+1, num_stations):
                a1 = positions[s1]
                a2 = positions[s2]
                distance = distance_between_points(a1[0], a1[1], a2[0], a2[1])
                index_writer.writerow([s1, s2, 1 if distance >= exclude_distance else 0])


def main():
    parser = argparse.ArgumentParser(description='Generate baseline index map for averager.')
    parser.add_argument('--ant', dest='antenna_file', required=True,
                        help='absolute antenna position file.')
    parser.add_argument('--dist', dest='exclude', default=6, type=int,
                        help='exclude baselines greater than or equal to a certain distance (km).')
    parser.add_argument('--out', dest='baseline_index_file', required=True,
                        help='baseline index file.')

    args = parser.parse_args()

    locations = parse_antenna_file(args.antenna_file)
    generate_baseline_index(locations, args.exclude, args.baseline_index_file)

if __name__ == '__main__':
    main()
