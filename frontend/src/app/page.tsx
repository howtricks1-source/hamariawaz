'use client'

import {
  Box,
  Button,
  Container,
  Flex,
  Heading,
  Text,
  VStack,
  HStack,
  Icon,
  Card,
  CardBody,
  SimpleGrid,
  useColorModeValue,
} from '@chakra-ui/react'
import { FaComments, FaUsers, FaChartLine, FaShieldAlt } from 'react-icons/fa'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/authStore'
import { useEffect } from 'react'

const features = [
  {
    icon: FaComments,
    title: 'Easy Complaint Submission',
    description: 'Submit complaints quickly and track their progress in real-time.',
  },
  {
    icon: FaUsers,
    title: 'Role-Based Access',
    description: 'Different access levels for students, staff, department heads, and administrators.',
  },
  {
    icon: FaChartLine,
    title: 'Analytics & Reports',
    description: 'Comprehensive analytics and reporting for better decision making.',
  },
  {
    icon: FaShieldAlt,
    title: 'Secure & Private',
    description: 'Your data is secure with role-based permissions and privacy controls.',
  },
]

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, user } = useAuthStore()
  const bgColor = useColorModeValue('gray.50', 'gray.900')
  const cardBg = useColorModeValue('white', 'gray.800')

  useEffect(() => {
    // Redirect authenticated users to their dashboard
    if (isAuthenticated && user) {
      switch (user.role) {
        case 'student':
          router.push('/student/dashboard')
          break
        case 'staff':
          router.push('/staff/dashboard')
          break
        case 'head':
          router.push('/head/dashboard')
          break
        case 'vc':
          router.push('/vc/dashboard')
          break
        case 'admin':
          router.push('/admin/dashboard')
          break
        default:
          router.push('/dashboard')
      }
    }
  }, [isAuthenticated, user, router])

  return (
    <Box bg={bgColor} minH="100vh">
      {/* Hero Section */}
      <Container maxW="7xl" py={20}>
        <VStack spacing={8} textAlign="center">
          <Heading
            as="h1"
            size="2xl"
            bgGradient="linear(to-r, brand.400, brand.600)"
            bgClip="text"
            fontWeight="bold"
          >
            Hamari Awaz
          </Heading>
          <Text fontSize="xl" color="gray.600" maxW="2xl">
            A comprehensive university complaint management system that empowers students
            to voice their concerns and helps authorities respond effectively.
          </Text>
          <HStack spacing={4}>
            <Button
              size="lg"
              colorScheme="brand"
              onClick={() => router.push('/login')}
            >
              Login
            </Button>
            <Button
              size="lg"
              variant="outline"
              colorScheme="brand"
              onClick={() => router.push('/register')}
            >
              Register as Student
            </Button>
          </HStack>
        </VStack>
      </Container>

      {/* Features Section */}
      <Container maxW="7xl" py={20}>
        <VStack spacing={12}>
          <VStack spacing={4} textAlign="center">
            <Heading as="h2" size="xl">
              Why Choose Hamari Awaz?
            </Heading>
            <Text fontSize="lg" color="gray.600" maxW="2xl">
              Our platform provides a seamless experience for managing university
              complaints and feedback with transparency and efficiency.
            </Text>
          </VStack>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={8}>
            {features.map((feature, index) => (
              <Card key={index} bg={cardBg} shadow="md" borderRadius="lg">
                <CardBody textAlign="center" p={8}>
                  <VStack spacing={4}>
                    <Icon
                      as={feature.icon}
                      w={12}
                      h={12}
                      color="brand.500"
                    />
                    <Heading as="h3" size="md">
                      {feature.title}
                    </Heading>
                    <Text color="gray.600" fontSize="sm">
                      {feature.description}
                    </Text>
                  </VStack>
                </CardBody>
              </Card>
            ))}
          </SimpleGrid>
        </VStack>
      </Container>

      {/* CTA Section */}
      <Box bg="brand.500" color="white" py={20}>
        <Container maxW="4xl" textAlign="center">
          <VStack spacing={6}>
            <Heading as="h2" size="xl">
              Ready to Get Started?
            </Heading>
            <Text fontSize="lg" opacity={0.9}>
              Join thousands of students and staff who are already using
              Hamari Awaz to make their voices heard.
            </Text>
            <HStack spacing={4}>
              <Button
                size="lg"
                bg="white"
                color="brand.500"
                _hover={{ bg: 'gray.100' }}
                onClick={() => router.push('/register')}
              >
                Register Now
              </Button>
              <Button
                size="lg"
                variant="outline"
                borderColor="white"
                color="white"
                _hover={{ bg: 'whiteAlpha.200' }}
                onClick={() => router.push('/about')}
              >
                Learn More
              </Button>
            </HStack>
          </VStack>
        </Container>
      </Box>

      {/* Footer */}
      <Box bg="gray.800" color="white" py={8}>
        <Container maxW="7xl">
          <Flex
            direction={{ base: 'column', md: 'row' }}
            justify="space-between"
            align="center"
            gap={4}
          >
            <Text>&copy; 2024 Hamari Awaz. All rights reserved.</Text>
            <HStack spacing={6}>
              <Button variant="link" color="white" size="sm">
                Privacy Policy
              </Button>
              <Button variant="link" color="white" size="sm">
                Terms of Service
              </Button>
              <Button variant="link" color="white" size="sm">
                Contact Us
              </Button>
            </HStack>
          </Flex>
        </Container>
      </Box>
    </Box>
  )
}

